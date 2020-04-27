import json
import re

from django.shortcuts import render, redirect
from django.db.models import Max, Avg, F, Q, Min, Count, Sum
from django.views.generic.base import View
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder

from utils.mixin_utils import LoginRequiredMixin
from rbac.models import Menu
from .models import WorkOrder, WorkOrderRecord, Order, MaternalSku, Stock
from .forms import WorkOrderCreateForm, WorkOrderUpdateForm, WorkOrderRecordForm, WorkOrderRecordUploadForm, \
    WorkOrderProjectUploadForm, OrderForm, OrderBackForm, OrderSendForm, OrderBugForm, OrderFinallyForm
from rbac.models import Role

from utils.toolkit import ToolKit, SendMessage

User = get_user_model()


class WorkOrderView(LoginRequiredMixin, View):
    """
        工单视图：根据前端请求的URL 分为个视图：我创建的工单、我审批的工单和我收到的工单====
    """

    def get(self, request):
        user = request.user
        power = [item.title for item in user.roles.all()]
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        status_list = []
        for order_status in Order.status_choices:
            status_dict = dict(item=order_status[0], value=order_status[1])
            status_list.append(status_dict)

        if "运营" in power:
            ret['status_list'] = status_list
        if "运营经理" in power:
            status_list.pop(1)
            ret['status_list'] = status_list[0:3]
        if "采购" in power:
            ret['status_list'] = status_list[3:5]
            return render(request, 'personal/order/order_bug.html', ret)
        if "仓库" in power:
            ret['status_list'] = status_list[5:]
            return render(request, 'personal/order/order_pack.html', ret)
        if "管理" in power:
            ret['status_list'] = status_list
        return render(request, 'personal/order/order.html', ret)


class WorkOrderListView(LoginRequiredMixin, View):
    """
        最重要的业务逻辑区(不同的用户取不同的值～)
        订单列表：通过前端传递回来的url来区分不同视图，返回相应列表数据====
    """

    def get(self, request):
        fields = ['system_sku', 'maternal_sku__sku', 'product_chinese_name', 'comparison_code', 'purchase_quantity',
                  'finish_status', 'status', 'remark', 'id', 'operation__name', 'purchase_link', 'order_quantity',
                  'lack', 'remark2', 'remark4', 'lack_warehouse_staff', 'issued_quantity']
        filters = dict()

        if 'system_sku' in request.GET and request.GET['system_sku']:
            filters['system_sku__icontains'] = request.GET['system_sku']
        if 'order_status' in request.GET and request.GET['order_status']:
            filters['status'] = request.GET['order_status']

        user = request.user
        power = [item.title for item in user.roles.all()]
        # if "运营" in power:
        #     filters['operation__id'] = user.id
        #     ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by('-add_time')))
        # if "采购" in power:
        #     filters['purchaser__id'] = user.id
        #     ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by('-add_time')))
        # if "仓库" in power:
        #     ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by('-add_time')))
        # if "运营经理" in power:
        #     filters['operation_manager__id'] = user.id
        #     ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by('-add_time')))
        # if "管理" in power:
        #     ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by('-add_time')))
        # if 'main_url' in request.GET and request.GET['main_url'] == '/personal/workorder_Icrt/':
        #     if "运营" in power:
        #         filters['operation__id'] = user.id
        #         filters['status__in'] = ['0', '1', '2']
        #     if "采购" in power:
        #         filters['purchaser__id'] = user.id
        #         filters['status__in'] = ['3']
        #     if "仓库" in power:
        #         # warehouse_staff__id=user.id
        #         filters['status__in'] = ['4']
        #     if "运营经理" in power:
        #         filters['operation_manager__id'] = user.id
        #         filters['status__in'] = ['0', '2']
        #     if "管理" in power:
        #         filters['status__in'] = ['0', '1', '2', '3', '4']
        #
        #     # filters['operation__id'] = request.user.id
        #     # filters['status__in'] = ['0', '1', '2']
        # if 'main_url' in request.GET and request.GET['main_url'] == '/personal/workorder_app/':
        #     if "运营" in power:
        #         filters['operation__id'] = user.id
        #         filters['status__in'] = ['3', '4', '5']
        #     if "采购" in power:
        #         filters['purchaser__id'] = user.id
        #         filters['status__in'] = ['4']
        #     if "仓库" in power:
        #         # warehouse_staff__id=user.id
        #         filters['status__in'] = ['5']
        #     if "运营经理" in power:
        #         filters['operation_manager__id'] = user.id
        #         filters['status__in'] = ['4', '5']
        #     if "管理" in power:
        #         filters['status__in'] = ['5']
        #     # filters['operation_manager__id'] = request.user.id
        #     # filters['status__in'] = ['0', '2', '3', '4', '5']  # 审批人视图可以看到的工单状态
        # if 'main_url' in request.GET and request.GET['main_url'] == '/personal/workorder_rec/':
        #     # filters['purchaser__id'] = request.user.id
        #     if not request.GET['order_status']:
        #         filters['status__in'] = ['0', '2', '3', '4', '5']
        #     ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by(
        #         '-add_time')))
        #     return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')

        if 'main_url' in request.GET and request.GET['main_url'] == '/personal/workorder_all/':
            # filters['operation__id'] = request.user.id
            # filters['operation_manager__id'] = request.user.id
            # filters['purchaser__id'] = request.user.id
            # filters['warehouse_staff__id'] = request.user.id
            # filters['status__in'] = ['0', '1', '2', '3', '4', '5']

            if "运营" in power:
                filters['operation__id'] = user.id
                filters['status__in'] = request.GET['order_status'] if request.GET['order_status'] else ['0', '1', '2', '3', '4', '6', '5']
            if "采购" in power:
                filters['purchaser__id'] = user.id
                filters['status__in'] = request.GET['order_status'] if request.GET['order_status'] else ['3', '4']
                # ret = dict(data=list(Order.objects.filter(**filters).values("system_sku", "status", "purchase_link", "finish_status", "product_chinese_name", "img").annotate(All_sum=Sum("purchase_quantity"))))
                sum_data = Order.objects.filter(**filters).values("system_sku", "status", "purchase_link",
                                                           "product_chinese_name", "img", "lack").annotate(
                        All_sum=Sum("purchase_quantity"))
                for item in sum_data:
                    item_msg = list(Order.objects.filter(system_sku=item.get("system_sku"), ).values("system_sku",  "product_chinese_name", "operation__username", "purchase_quantity", "operation_manager__username"))
                    item["child"] = item_msg
                ret = dict(data=list(sum_data))
                return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')
            if "仓库" in power:
                # warehouse_staff__id=user.id
                if request.GET.get("other"):
                    filters['status__in'] = request.GET['order_status'] if request.GET['order_status'] else ['6', '4']
                    ret = dict(data=list(Order.objects.filter(**filters).values("system_sku", "product_chinese_name", "lack_warehouse_staff", "status").annotate(
                        All_sum=Sum("purchase_quantity"))))
                    # ret = dict(data=list(Order.objects.filter(**filters).values(
                    #     "maternal_sku__sku", "system_sku", "product_chinese_name", "status", "operation__username", "operation_manager__username", "purchase_link", "purchase_quantity",
                    #     "finish_status", "lack", "order_quantity", "remark4", "lack_warehouse_staff", "id").order_by("system_sku")))
                    return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')
                filters['status__in'] = request.GET['order_status'] if request.GET['order_status'] else ['6', '5']
            if "运营经理" in power:
                filters['operation_manager__id'] = user.id
                filters['status__in'] = request.GET['order_status'] if request.GET['order_status'] else ['0', '2', '3']
            if "管理" in power:
                filters['status__in'] = request.GET['order_status'] if request.GET['order_status'] else ['0', '1', '2', '3', '4', '5', '6']
            # if not request.GET['order_status']:
            #     filters['status__in'] = ['0', '1', '2', '3', '4', '5']
            ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by(
                'system_sku',
                '-add_time')))
            return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')
        ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by('-add_time')))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


# 创建
class WorkOrderCreateView(LoginRequiredMixin, View):
    def get(self, request):
        type_list = []
        for order_type in Order.finish_status_choices:
            type_dict = dict(item=order_type[0], value=order_type[1])
            type_list.append(type_dict)

        operation_manager = request.user.superior if request.user.superior else request.user
        try:
            number = Order.objects.latest('order_number').order_number
        except Order.DoesNotExist:
            number = ""
        new_number = ToolKit.bulidNumber('SX', 9, number)
        purchase_name = User.objects.filter(roles__title="采购").values('id', 'name')
        ret = {
            'type_list': type_list,
            'operation_manager': operation_manager,
            'new_number': new_number,
            "purchase_list": purchase_name
        }
        return render(request, 'personal/order/order_create.html', ret)

    def post(self, request):
        res = dict()
        order = Order()
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

        order_form = OrderForm(request.POST, request.FILES, instance=order)
        if order_form.is_valid():
            order_form.save()
            res['status'] = 'success'
            if order.status == "2":
                res['status'] = 'submit'
                try:
                    SendMessage.send_workorder_email(request.POST['number'])
                    res['status'] = 'submit_send'
                except Exception:
                    pass
        else:
            pattern = '<li>.*?<ul class=.*?><li>(.*?)</li>'
            errors = str(order_form.errors)
            work_order_form_errors = re.findall(pattern, errors)
            res = {
                'status': 'fail',
                'work_order_form_errors': work_order_form_errors[0]
            }
        return HttpResponse(json.dumps(res), content_type='application/json')


# 详情
class WorkOrderDetailView(LoginRequiredMixin, View):

    def get(self, request):
        ret = dict()
        admin_user_list = []
        # user = request.user
        # power = [item.title for item in user.roles.all()]
        if 'id' in request.GET and request.GET['id']:
            work_order = get_object_or_404(Order, pk=request.GET['id'])
            # try:
            #     role = Role.objects.get(title="运营经理")
            #     admin_user_ids = role.userprofile_set.values('id')
            #     for admin_user_id in admin_user_ids:
            #         admin_user_list.append(admin_user_id['id'])
            # except Exception:
            #     pass
            ret['work_order'] = work_order
        return render(request, 'personal/workorder/workorder_detail.html', ret)
        # if "运营经理" in power:
        #     if 'id' in request.GET and request.GET['id']:
        #         work_order = get_object_or_404(Order, pk=request.GET['id'])
        #         try:
        #             role = Role.objects.get(title="运营经理")
        #             admin_user_ids = role.userprofile_set.values('id')
        #             for admin_user_id in admin_user_ids:
        #                 admin_user_list.append(admin_user_id['id'])
        #         except Exception:
        #             pass
        #         ret['work_order'] = work_order
        #     return render(request, 'personal/workorder/workorder_detail.html', ret)
        # if "采购" in power:
        #     if 'id' in request.GET and request.GET['id']:
        #         work_order = get_object_or_404(Order, pk=request.GET['id'])
        #         try:
        #             role = Role.objects.get(title="采购")
        #             admin_user_ids = role.userprofile_set.values('id')
        #             for admin_user_id in admin_user_ids:
        #                 admin_user_list.append(admin_user_id['id'])
        #         except Exception:
        #             pass
        #         ret['work_order'] = work_order
        #     return render(request, 'personal/order/order_bug_detail.html', ret)
        # if "仓库" in power:
        #     if 'id' in request.GET and request.GET['id']:
        #         work_order = get_object_or_404(Order, pk=request.GET['id'])
        #         try:
        #             role = Role.objects.get(title="仓库")
        #             admin_user_ids = role.userprofile_set.values('id')
        #             for admin_user_id in admin_user_ids:
        #                 admin_user_list.append(admin_user_id['id'])
        #         except Exception:
        #             pass
        #         ret['work_order'] = work_order
        #     return render(request, 'personal/order/order_storehouse_detail.html', ret)

        # if 'id' in request.GET and request.GET['id']:
        #     work_order = get_object_or_404(Order, pk=request.GET['id'])
        #     try:
        #         role = Role.objects.get(title="运营经理")
        #         admin_user_ids = role.userprofile_set.values('id')
        #         for admin_user_id in admin_user_ids:
        #             admin_user_list.append(admin_user_id['id'])
        #     except Exception:
        #         pass
        #     ret['work_order'] = work_order
        # return render(request, 'personal/workorder/workorder_detail.html', ret)


# 删除
class WorkOrderDeleteView(LoginRequiredMixin, View):
    """
        删除订单====
    """

    def post(self, request):
        ret = dict(result=False)
        if 'id' in request.POST and request.POST['id']:
            status = get_object_or_404(Order, pk=request.POST['id']).status
            if int(status) <= 1:
                id_list = map(int, request.POST.get('id').split(','))
                Order.objects.filter(id__in=id_list).delete()
                ret['result'] = True
        return HttpResponse(json.dumps(ret), content_type='application/json')


# 更新
class WorkOrderUpdateView(LoginRequiredMixin, View):
    """
        订单更新=====
    """

    def get(self, request):
        status_list = []
        type_list = []
        for order_type in Order.finish_status_choices:
            type_dict = dict(item=order_type[0], value=order_type[1])
            type_list.append(type_dict)
        if 'id' in request.GET and request.GET['id']:
            order = get_object_or_404(Order, pk=request.GET['id'])
        # 防止审核状态中更数据或者其他状态下更改数据
        if int(order.status) not in [0, 1, 2]:
            return redirect("/404")
        for order_status in Order.status_choices:
            status_dict = dict(item=order_status[0], value=order_status[1])
            status_list.append(status_dict)
        purchase_name = User.objects.filter(roles__title="采购").values('id', 'name')
        operation_manager = request.user.superior if request.user.superior else request.user
        ret = {
            'order': order,
            'status_list': status_list,
            'operation_manager': operation_manager,
            'type_list': type_list,
            "purchase_list": purchase_name
        }
        return render(request, 'personal/workorder/workorder_update.html', ret)

    def post(self, request):
        res = dict()
        work_order = get_object_or_404(Order, pk=request.POST['id'])
        MaternalSku.objects.filter(id=work_order.maternal_sku_id).update(sku=request.POST['maternal_sku'])
        work_order_form = WorkOrderUpdateForm(request.POST, request.FILES, instance=work_order)
        if int(work_order.status) <= 1:
            if work_order_form.is_valid():
                work_order_form.save()
                res['status'] = 'success'
                if work_order.status == "2":
                    res['status'] = 'submit'
            else:
                pattern = '<li>.*?<ul class=.*?><li>(.*?)</li>'
                errors = str(work_order_form.errors)
                work_order_form_errors = re.findall(pattern, errors)
                res = {
                    'status': 'fail',
                    'work_order_form_errors': work_order_form_errors[0]
                }
        else:
            res['status'] = 'ban'
        return HttpResponse(json.dumps(res), content_type='application/json')


# 派发
class WorkOrderSendView(LoginRequiredMixin, View):
    """
        订单派发:运营经理完成 派发运营的订单给采购，
    """

    def get(self, request):
        # 判断是否是从库存页面进来  直接给打包～
        is_store = Order.objects.filter(purchase_status=1, id=request.GET['id'])
        if is_store:
            is_store.update(status=4)
            msg = "提交成功！"
            return render(request, 'personal/workorder/workorder_ok.html', {"msg": msg})
        ret = dict()
        engineers = User.objects.filter(roles__title='采购')
        work_order = get_object_or_404(Order, pk=request.GET['id'])
        ret['engineers'] = engineers
        ret['work_order'] = work_order
        ret['status'] = "3"
        return render(request, 'personal/workorder/workorder_send.html', ret)

    def post(self, request):
        res = dict(status='fail')
        work_order = get_object_or_404(Order, pk=request.POST['id'])
        work_order_record_form = OrderSendForm(request.POST, instance=work_order)
        if work_order_record_form.is_valid():
            if request.user.id == work_order.operation_manager_id:
                work_order_record_form.save()
                res['status'] = 'success'
                try:
                    SendMessage.send_workorder_email(request.POST['order_number'])
                    res['status'] = 'success_send'
                except Exception:
                    pass

            else:
                res['status'] = 'ban'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


# 采购
class WorkOrderExecuteView(LoginRequiredMixin, View):
    """
    采购提交
    """

    def get(self, request):
        ret = dict()
        work_order = get_object_or_404(Order, pk=request.GET['id'])
        ret['order'] = work_order
        ret['record_type'] = "2"
        return render(request, 'personal/workorder/workorder_execute.html', ret)

    def post(self, request):
        order_quantity = request.POST.get("order_quantity")
        lack = request.POST.get("lack")
        remark2 = request.POST.get("remark2")
        system_sku = request.POST.get("system_sku")
        if int(lack) == 0:
            Order.objects.filter(purchaser__id=request.user.id, status='3', system_sku=system_sku).update(status="4", order_quantity=order_quantity)
        elif int(lack) > 0:
            pass
        res = {"code": 1000}
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


# 打包仓库
class WorkOrderFinishView(LoginRequiredMixin, View):

    def get(self, request):
        ret = dict()
        work_order = get_object_or_404(Order, pk=request.GET['id'])
        # 防止其他状态下的提交
        if work_order.status != "4":
            return redirect("/404")
        ret['order'] = work_order
        return render(request, 'personal/workorder/workorder_finish.html', ret)

    def post(self, request):
        res = dict(status='fail')
        res["code"] = 1000
        work_order = get_object_or_404(Order, pk=request.POST['id'])
        # 防止其他状态下的提交
        if work_order.status != "6":
            print("=============")
            res['code'] = 1001
            return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')
        work_order_record_form = OrderFinallyForm(request.POST, instance=work_order)
        if work_order_record_form.is_valid():
            if work_order.status == "5":  # request.user.id == work_order.warehouse_staff_id
                if request.POST.get("lack", 0) == 0:
                    is_item = Stock.objects.filter(system_sku=work_order.system_sku)
                    if is_item:
                        issued_quantity = work_order.issued_quantity
                        is_item.update(stock_quantity=int(is_item[0].stock_quantity)-int(issued_quantity))
                else:
                    # ===============
                    pass
                work_order_record_form.save()
                res['status'] = 'success'
                try:
                    SendMessage.send_workorder_email(request.POST['number'])
                    res['status'] = 'success_send'
                except Exception as e:
                    pass
            else:
                res['status'] = 'ban'

        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


class WorkOrderReturnView(LoginRequiredMixin, View):

    def get(self, request):
        ret = dict()
        work_order = get_object_or_404(Order, pk=request.GET['id'])
        ret['order'] = work_order
        ret['status'] = "0"
        return render(request, 'personal/workorder/workorder_return.html', ret)

    def post(self, request):
        res = dict(status='fail')
        # work_order_record_form = OrderBackForm(request.POST)
        work_order = get_object_or_404(Order, pk=request.POST['id'])
        work_order_record_form = OrderBackForm(request.POST, instance=work_order)
        if work_order_record_form.is_valid():
            status = work_order.status
            work_order_record_form.save()
            work_order.status = "0"
            work_order.save()
            res['status'] = 'success'
            try:
                SendMessage.send_workorder_email(request.POST['number'])
                res['status'] = 'success_send'
            except Exception as e:
                pass
            work_order.save()
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


# 质检
class WorkOrderTrueView(LoginRequiredMixin, View):

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        status_list = []
        for order_status in Order.status_choices:
            status_dict = dict(item=order_status[0], value=order_status[1])
            status_list.append(status_dict)
        ret['status_list'] = status_list[4:-2]
        return render(request, 'personal/order/true_order.html', ret)

    def post(self, request):
        order_quantity = request.POST.get("order_quantity", 0)
        lack_warehouse_staff = request.POST.get("lack", 0)
        remark4 = request.POST.get("remark2")
        system_sku = request.POST.get("system_sku")
        position = request.POST.get("position")
        # 不缺少
        if int(lack_warehouse_staff) == 0:
            good_order = Order.objects.filter(status='4', system_sku=system_sku)
            if good_order:
                good_order.update(status="6", remark4=remark4, lack_warehouse_staff=lack_warehouse_staff, position=position)
                # 商品入库
                is_item = Stock.objects.filter(system_sku=system_sku)
                if is_item:
                    is_item.update(stock_quantity=int(is_item[0].stock_quantity) + int(order_quantity))
                else:
                    Stock.objects.create(stock_quantity=order_quantity,
                                         system_sku=good_order.system_sku, order_number=good_order.order_number,
                                         purchase_link=good_order.purchase_link,
                                         product_chinese_name=good_order.product_chinese_name, img=good_order.img,
                                         position=position, comparison_code=good_order.comparison_code)
                res = {"code": 1000}
            else:
                res = {"code": 1001, "data": "请勿重复操作！"}
        # 瞎搞  乱填
        elif int(lack_warehouse_staff) < 0:
            res = {"code": "请不要乱输入哦"}
        # 缺少
        else:
            good_order = Order.objects.filter(status='4', system_sku=system_sku)
            if good_order:
                # 问题产品
                good_order.update(status="7", remark4=remark4, lack_warehouse_staff=lack_warehouse_staff,
                                  position=position)
                # 商品入库
                is_item = Stock.objects.filter(system_sku=system_sku)
                if is_item:
                    is_item.update(stock_quantity=int(is_item[0].stock_quantity) + int(order_quantity))
                else:
                    Stock.objects.create(stock_quantity=order_quantity,
                                         system_sku=good_order.system_sku, order_number=good_order.order_number,
                                         purchase_link=good_order.purchase_link,
                                         product_chinese_name=good_order.product_chinese_name, img=good_order.img,
                                         position=position, comparison_code=good_order.comparison_code)
                res = {"code": 1000}
            else:
                res = {"code": 1001, "data": "请勿重复操作！"}
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


class WorkOrderAllTrueView(LoginRequiredMixin, View):

    def get(self, request):
        return render(request, 'personal/order/true_all_order.html')


class WorkOrderGetView(LoginRequiredMixin, View):
    def get(self, request):
        fields = ['system_sku', 'maternal_sku__sku', 'product_chinese_name', 'comparison_code', 'purchase_quantity',
                  'finish_status', 'status', 'remark', 'id', "operation__name", 'add_time', 'is_store']
        if request.GET.get('url') == "all":
            ret = dict(data=list(Order.objects.filter(purchase_status="0").values(*fields).order_by('-add_time')))
        else:
            ret = dict(data=list(Order.objects.filter(status="4", purchase_status="0", is_store="0").values(*fields).order_by('-add_time')))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')

    def post(self, request):
        id = request.POST.get('id')
        Order.objects.filter(id=id).update(is_store='1')
        ret = {"code": 200}
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class WorkOrderUploadView(LoginRequiredMixin, View):
    """
    上传配置资料：工单执行记录配置资料上传
    """

    def get(self, request):
        ret = dict()
        work_order = get_object_or_404(WorkOrder, pk=request.GET['id'])
        ret['work_order'] = work_order
        return render(request, 'personal/workorder/workorder_upload.html', ret)

    def post(self, request):
        res = dict(status='fail')
        # work_order_record = get_object_or_404(WorkOrderRecord, name_id=request.user.id, work_order_id=request.POST['id'])
        filters = dict(name_id=request.user.id, work_order_id=request.POST['id'])
        work_order_record = WorkOrderRecord.objects.filter(**filters).last()
        work_order_record_upload_form = WorkOrderRecordUploadForm(request.POST, request.FILES,
                                                                  instance=work_order_record)
        if work_order_record_upload_form.is_valid():
            work_order_record_upload_form.save()
            res['status'] = 'success'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


class WorkOrderProjectUploadView(LoginRequiredMixin, View):
    """
    上传项目资料：工单内容项目资料上传
    """

    def get(self, request):
        ret = dict()
        work_order = get_object_or_404(WorkOrder, pk=request.GET['id'])
        ret['work_order'] = work_order
        return render(request, 'personal/workorder/workorder_project_upload.html', ret)

    def post(self, request):
        res = dict(status='fail')
        work_order = get_object_or_404(WorkOrder, pk=request.POST['id'])
        work_order_project_upload_form = WorkOrderProjectUploadForm(request.POST, request.FILES, instance=work_order)
        if work_order_project_upload_form.is_valid() and request.user.id == work_order.proposer_id:
            work_order_project_upload_form.save()
            res['status'] = 'success'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


class WorkOrderDocumentView(LoginRequiredMixin, View):
    """
    工单文档
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)

        return render(request, 'personal/workorder/document.html', ret)


class WorkOrderDocumentListView(LoginRequiredMixin, View):
    """
    工单文档列表
    """

    def get(self, request):
        fields = ['work_order__number', 'work_order__customer__unit', 'name__name', 'add_time', 'file_content']
        ret = dict(data=list(WorkOrderRecord.objects.filter(~Q(file_content='')).values(*fields).order_by('-add_time')))

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')
