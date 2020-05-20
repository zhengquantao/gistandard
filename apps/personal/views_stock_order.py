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
from .models import Order, StockOrder, MaternalSku, SkuToUrl
from .forms import StockOrderForm
from rbac.models import Role

User = get_user_model()


# 查询链接
class StockOrderView(LoginRequiredMixin, View):
    """
        工单视图：根据前端请求的URL 分为个视图：我创建的工单、我审批的工单和我收到的工单====
    """

    def get(self, request):
        system_sku = request.GET.get("system_sku")
        ret = dict(data=list(SkuToUrl.objects.filter(sku=system_sku).values("id", "sku", "url", "supplier", "status")))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


# 增加链接
class StockOrderListView(LoginRequiredMixin, View):
    """
    工单列表：通过前端传递回来的url来区分不同视图，返回相应列表数据
    """
    def post(self, request):
        # fields = ['id', 'system_sku', 'maternal_sku__sku', 'order_quantity', 'status', 'add_time', 'operation__name', 'operation_manager__name']
        # filters = dict()
        # if 'main_url' in request.GET and request.GET['main_url'] == '/personal/stockorder_Icrt/':
        #     filters['proposer_id'] = request.user.id
        # if 'main_url' in request.GET and request.GET['main_url'] == '/personal/stockorder_app/':
        #     filters['approver_id'] = request.user.id
        #     filters['status__in'] = ['0', '2', '3', '4', '5']  # 审批人视图可以看到的工单状态
        # if 'main_url' in request.GET and request.GET['main_url'] == '/personal/stockorder_rec/':
        #     filters['receiver_id'] = request.user.id
        # if 'number' in request.GET and request.GET['number']:
        #     filters['number__icontains'] = request.GET['number']
        # if 'workorder_status' in request.GET and request.GET['stockorder_status']:
        #     filters['status'] = request.GET['workorder_status']
        # ret = dict(data=list(StockOrder.objects.filter(**filters).values(*fields).order_by('-add_time')))
        system_sku = request.POST.get("system_sku")
        url = request.POST.get("url")
        supplier = request.POST.get("supplier")
        # SkuToUrl.objects.create(sku=system_sku, url=url, supplier=supplier)
        sku_to_url = SkuToUrl(sku=system_sku, url=url, supplier=supplier)
        sku_to_url.save()
        ret = {"code": 1000, "id": sku_to_url.id}
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class StockOrderToLinkView(LoginRequiredMixin, View):
    def get(self, request):
        # role = get_object_or_404(Role, title='运营经理')
        # approver = role.userprofile_set.all()
        system_sku = request.GET.get("system_sku")
        object_set = SkuToUrl.objects.filter(sku=system_sku, status="1").values("id", "sku", "url")
        if not object_set:
            object_set = SkuToUrl.objects.filter(sku=system_sku).order_by('-id').values("id", "sku", "url")
            if not object_set:
                object_set = ""
        ret = dict(data=list(object_set))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


# 新建库存订单
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
        stock_order = StockOrder()
        maternal_sku = request.POST.get('maternal_sku', "")
        if maternal_sku:
            maternal_sku_object = MaternalSku.objects.filter(sku=maternal_sku).first()
            if not maternal_sku_object:
                maternal_sku_object = MaternalSku(sku=maternal_sku)
                maternal_sku_object.save()
            data = request.POST
            # 记住旧的方式
            _mutable = data._mutable
            # 设置_mutable为True
            data._mutable = True
            # 改变你想改变的数据
            data['maternal_sku'] = maternal_sku_object.id
            # 恢复_mutable原来的属性
            data._mutable = _mutable

        stock_order_form = StockOrderForm(request.POST, instance=stock_order)
        if stock_order_form.is_valid():
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


# 删除链接
class StockOrderDeleteView(LoginRequiredMixin, View):
    """
        删除订单====
    """
    def post(self, request):
        ret = dict(result=False)
        # if 'id' in request.POST and request.POST['id']:
        #     status = get_object_or_404(StockOrder, pk=request.POST['id']).status
        #     if int(status) <= 1:
        #         id_list = map(int, request.POST.get('id').split(','))
        #         StockOrder.objects.filter(id__in=id_list).delete()
        #         ret['result'] = True
        id = request.POST.get("id")
        SkuToUrl.objects.filter(id=id).delete()
        ret["code"] = 1000
        return HttpResponse(json.dumps(ret), content_type='application/json')


# 标为常用
class StockOrderEditView(LoginRequiredMixin, View):
    def post(self, request):
        ret = dict(result=False)
        s_id = request.POST.get("id")
        # print(id)
        sku_to_url = SkuToUrl.objects.filter(id=s_id).first()
        SkuToUrl.objects.filter(sku=sku_to_url.sku).update(status='0')
        sku_to_url.status = "1"
        sku_to_url.save()
        ids = dict(data=list(SkuToUrl.objects.filter(sku=sku_to_url.sku).exclude(id=s_id).values("id")))
        ret["code"] = 1000
        ret["id"] = s_id
        ret["ids"] = ids
        return HttpResponse(json.dumps(ret), content_type='application/json')


# 更新库存
class StockOrderUpdateView(LoginRequiredMixin, View):
    """
        更新=====
    """
    def get(self, request):
        status_list = []
        if 'id' in request.GET and request.GET['id']:
            stock_order = get_object_or_404(StockOrder, pk=request.GET['id'])
        for stock_order_status in StockOrder.status_choices:
            status_dict = dict(item=stock_order_status[0], value=stock_order_status[1])
            status_list.append(status_dict)

        operation_manager = request.user.superior if request.user.superior else request.user
        ret = {
            'order': stock_order,
            'status_list': status_list,
            'operation_manager': operation_manager,
        }
        return render(request, 'personal/stockorder/stockorder_update.html', ret)

    def post(self, request):
        res = dict()
        id = request.POST.get("id")
        number = request.POST.get("number")

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

