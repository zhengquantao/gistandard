import json
import re

from django.shortcuts import render
from django.db.models import Q
from django.views.generic.base import View
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder

from utils.mixin_utils import LoginRequiredMixin
from rbac.models import Menu
from .forms import StockCreateForm, StockUpdateForm, StockOrderForm
from .models import Stock, Order, MaternalSku, StockLog
from rbac.models import Role
from utils.toolkit import ToolKit, SendMessage

User = get_user_model()


class StockView(LoginRequiredMixin, View):
    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        return render(request, 'personal/stock/stock.html', ret)


class StockListView(LoginRequiredMixin, View):
    def get(self, request):
        fields = ['id', 'system_sku', 'stock_quantity', 'maternal_sku__sku', 'product_chinese_name', 'purchase_link']
        filters = dict()
        sku = request.GET.get('number')
        if sku:
            filters['system_sku__icontains'] = sku
        ret = dict(data=list(Stock.objects.filter(stock_quantity__gt=0, **filters).values(*fields).order_by('-add_time')))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


# 录入商品库存
class StockCreateView(LoginRequiredMixin, View):
    """
    这个是让仓库人员要录入之前有库存的～～～～
    """
    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        type_list = []
        for stock_type in Stock.finish_status_choices:
            type_dict = dict(item=stock_type[0], value=stock_type[1])
            type_list.append(type_dict)

        ret['type_list'] = type_list
        return render(request, 'personal/stock/stock_create.html', ret)

    def post(self, request):
        res = dict()
        stock = Stock()
        stock_form = StockCreateForm(request.POST, instance=stock)
        if stock_form.is_valid():
            stock_form.save()
            res['status'] = 'success'
        else:
            pattern = '<li>.*?<ul class=.*?><li>(.*?)</li>'
            errors = str(stock_form.errors)
            stock_form_errors = re.findall(pattern, errors)
            res = {
                'status': 'fail',
                'stock_form_errors': stock_form_errors[0]
            }
        return HttpResponse(json.dumps(res), content_type='application/json')


# 删除库存
class StockDeleteView(LoginRequiredMixin, View):
    def post(self, request):
        ret = dict(result=False)
        if 'id' in request.POST and request.POST['id']:
            id_list = map(int, request.POST.get('id').split(','))
            Stock.objects.filter(id__in=id_list).delete()
            ret['result'] = True
        return HttpResponse(json.dumps(ret), content_type='application/json')


# 运营创建库存订单
class StockUpdateView(LoginRequiredMixin, View):

    def get(self, request):
        if request.GET.get("compose"):
            operation_manager = request.user.superior if request.user.superior else request.user
            try:
                number = Order.objects.latest('order_number').order_number
            except Order.DoesNotExist:
                number = ""
            new_number = ToolKit.bulidNumber('SX', 9, number)
            ret = {
                'operation_manager': operation_manager,
                'new_number': new_number,
            }
            return render(request, "personal/stock/stock_update_compose.html", ret)
        type_list = []
        if 'id' in request.GET and request.GET['id']:
            stock = get_object_or_404(Stock, pk=request.GET['id'])
        for stock_type in Stock.finish_status_choices:
            type_dict = dict(item=stock_type[0], value=stock_type[1])
            type_list.append(type_dict)
        operation_manager = request.user.superior if request.user.superior else request.user
        try:
            number = Order.objects.latest('order_number').order_number
        except Order.DoesNotExist:
            number = ""
        new_number = ToolKit.bulidNumber('SX', 9, number)
        ret = {
            'type_list': type_list,
            'operation_manager': operation_manager,
            'new_number': new_number,
            'stock': stock
        }
        return render(request, 'personal/stock/stock_update.html', ret)

    def post(self, request):
        res = dict()
        stock = get_object_or_404(Stock, pk=request.POST['id'])
        stock_form = StockUpdateForm(request.POST, instance=stock)
        if stock_form.is_valid():
            stock_form.save()
            res['status'] = 'success'
        else:
            pattern = '<li>.*?<ul class=.*?><li>(.*?)</li>'
            errors = str(stock_form.errors)
            stock_form_errors = re.findall(pattern, errors)
            res = {
                'status': 'fail',
                'stock_form_errors': stock_form_errors[0]
            }
        return HttpResponse(json.dumps(res), content_type='application/json')


# 其他人员增加库存
class StockOrderCreateView(LoginRequiredMixin, View):
    def get(self, request):
        # role = get_object_or_404(Role, title='运营经理')
        # approver = role.userprofile_set.all()
        operation_manager = request.user.superior if request.user.superior else request.user
        ret = {
            'operation_manager': operation_manager
        }
        return render(request, 'personal/stockorder/stockorder_create.html', ret)

    def post(self, request):
        res = dict()
        stock_order = Stock()
        maternal_sku = request.POST.get('maternal_sku', "")
        if maternal_sku:
            maternal_sku_object = MaternalSku.objects.filter(sku=maternal_sku).first()
            if not maternal_sku_object:
                maternal_sku_object = MaternalSku(sku=maternal_sku)
                maternal_sku_object.save()
        stock_order_form = StockCreateForm(request.POST, instance=stock_order)
        if stock_order_form.is_valid():
            # 放入日志表中
            StockLog.objects.create(user=request.user.name, after_number=request.POST['stock_quantity'],
                                    before_number=0, sku=request.POST['system_sku'],
                                    sku_name=request.POST['product_chinese_name'], content="增加")
            stock_order_form.save()
            res['status'] = 'success'
        else:
            pattern = '<li>.*?<ul class=.*?><li>(.*?)</li>'
            errors = str(stock_order_form.errors)
            stock_order_form_errors = re.findall(pattern, errors)
            res = {
                'status': 'fail',
                'stock_order_form_errors': stock_order_form_errors[0]
            }
        return HttpResponse(json.dumps(res), content_type='application/json')


# 更新库存
class StockOrderUpdateView(LoginRequiredMixin, View):
    """
        更新=====
    """
    # def get(self, request):
    #     status_list = []
    #     if 'id' in request.GET and request.GET['id']:
    #         stock_order = get_object_or_404(StockOrder, pk=request.GET['id'])
    #     for stock_order_status in StockOrder.status_choices:
    #         status_dict = dict(item=stock_order_status[0], value=stock_order_status[1])
    #         status_list.append(status_dict)
    #
    #     operation_manager = request.user.superior if request.user.superior else request.user
    #     ret = {
    #         'order': stock_order,
    #         'status_list': status_list,
    #         'operation_manager': operation_manager,
    #     }
    #     return render(request, 'personal/stockorder/stockorder_update.html', ret)

    def post(self, request):
        res = dict()
        res = dict()
        id = request.POST.get("id")
        number = request.POST.get("number")
        is_num = Stock.objects.filter(id=id)
        before_num = is_num.values("stock_quantity")
        is_num.update(stock_quantity=number)
        # 放入日志表中
        StockLog.objects.create(user=request.user.name, after_number=number,
                                before_number=is_num[0].stock_quantity, sku=is_num[0].system_sku,
                                sku_name=is_num[0].product_chinese_name, content="更改")

        res["code"] = 1000
        # stock_order = get_object_or_404(StockOrder, pk=request.POST['id'])
        #
        # maternal_sku = request.POST.get('maternal_sku', "")
        # if maternal_sku:
        #     maternal_sku_object = MaternalSku.objects.filter(sku=maternal_sku).first()
        #     if not maternal_sku_object:
        #         maternal_sku_object = MaternalSku(sku=maternal_sku)
        #         maternal_sku_object.save()
        #     data = request.POST
        #     # 记住旧的方式
        #     _mutable = data._mutable
        #     # 设置_mutable为True
        #     data._mutable = True
        #     # 改变你想改变的数据
        #     data['maternal_sku'] = maternal_sku_object.id
        #     # 恢复_mutable原来的属性
        #     data._mutable = _mutable
        #
        # stock_order_form = StockOrderForm(request.POST, instance=stock_order)
        # if int(stock_order.status) <= 1:
        #     if stock_order_form.is_valid():
        #         stock_order_form.save()
        #         res['status'] = 'success'
        #     else:
        #         pattern = '<li>.*?<ul class=.*?><li>(.*?)</li>'
        #         errors = str(stock_order_form.errors)
        #         stock_order_form_errors = re.findall(pattern, errors)
        #         res = {
        #             'status': 'fail',
        #             'stock_order_form_errors': stock_order_form_errors[0]
        #         }
        # else:
        #     res['status'] = 'ban'
        return HttpResponse(json.dumps(res), content_type='application/json')

