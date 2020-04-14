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
from .models import WorkOrder, WorkOrderRecord, Order, MaternalSku
from .forms import WorkOrderCreateForm, WorkOrderUpdateForm, WorkOrderRecordForm, WorkOrderRecordUploadForm, WorkOrderProjectUploadForm, OrderForm, OrderBackForm, OrderSendForm, OrderBugForm, OrderFinallyForm
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

        if "采购" in power:
            ret['status_list'] = Order.objects.filter(status='3')
            return render(request, 'personal/order/order_bug.html', ret)

        if "仓库" in power:
            ret['status_list'] = Order.objects.filter(status='3')
            return render(request, 'personal/order/order_storehouse.html', ret)

        if "运营经理" in power:
            for order_status in Order.status_choices:
                status_dict = dict(item=order_status[0], value=order_status[1])
                status_list.append(status_dict)
            ret['status_list'] = status_list
            return render(request, 'personal/order/order_manager.html', ret)

        if "管理" in power:
            for order_status in Order.status_choices:
                status_dict = dict(item=order_status[0], value=order_status[1])
                status_list.append(status_dict)
            ret['status_list'] = status_list
            return render(request, 'personal/order/order_manager.html', ret)

        for order_status in Order.status_choices:
            status_dict = dict(item=order_status[0], value=order_status[1])
            status_list.append(status_dict)
        ret['status_list'] = status_list
        return render(request, 'personal/order/order.html', ret)


class WorkOrderListView(LoginRequiredMixin, View):
    """
        工单列表：通过前端传递回来的url来区分不同视图，返回相应列表数据====
    """

    def get(self, request):
        fields = ['system_sku', 'maternal_sku__sku','product_chinese_name', 'comparison_code', 'purchase_quantity',
                  'finish_status', 'status', 'remark', 'id', "operation__name"]
        filters = dict()

        if 'system_sku' in request.GET and request.GET['system_sku']:
            filters['system_sku__icontains'] = request.GET['system_sku']
        if 'order_status' in request.GET and request.GET['order_status']:
            filters['status'] = request.GET['order_status']

        user = request.user
        power = [item.title for item in user.roles.all()]
        if "运营" in power:
            filters['operation__id'] = user.id
            ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by('-add_time')))
        if "采购" in power:
            filters['purchaser__id'] = user.id
            ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by('-add_time')))
        if "仓库" in power:
            ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by('-add_time')))
        if "运营经理" in power:
            filters['operation_manager__id'] = user.id
            ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by('-add_time')))
        if "管理" in power:
            ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by('-add_time')))
        # ret = dict(data=list(Order.objects.filter(**filters).values(*fields).order_by('-add_time')))

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


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
        ret = {
            'type_list': type_list,
            'operation_manager': operation_manager,
            'new_number': new_number
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

        order_form = OrderForm(request.POST,  request.FILES, instance=order)
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


class WorkOrderDetailView(LoginRequiredMixin, View):

    def get(self, request):
        ret = dict()
        admin_user_list = []
        user = request.user
        power = [item.title for item in user.roles.all()]
        if "运营经理" in power:
            if 'id' in request.GET and request.GET['id']:
                work_order = get_object_or_404(Order, pk=request.GET['id'])
                try:
                    role = Role.objects.get(title="运营经理")
                    admin_user_ids = role.userprofile_set.values('id')
                    for admin_user_id in admin_user_ids:
                        admin_user_list.append(admin_user_id['id'])
                except Exception:
                    pass
                ret['work_order'] = work_order
            return render(request, 'personal/workorder/workorder_detail.html', ret)
        if "采购" in power:
            if 'id' in request.GET and request.GET['id']:
                work_order = get_object_or_404(Order, pk=request.GET['id'])
                try:
                    role = Role.objects.get(title="采购")
                    admin_user_ids = role.userprofile_set.values('id')
                    for admin_user_id in admin_user_ids:
                        admin_user_list.append(admin_user_id['id'])
                except Exception:
                    pass
                ret['work_order'] = work_order
            return render(request, 'personal/order/order_bug_detail.html', ret)
        if "仓库" in power:
            if 'id' in request.GET and request.GET['id']:
                work_order = get_object_or_404(Order, pk=request.GET['id'])
                try:
                    role = Role.objects.get(title="仓库")
                    admin_user_ids = role.userprofile_set.values('id')
                    for admin_user_id in admin_user_ids:
                        admin_user_list.append(admin_user_id['id'])
                except Exception:
                    pass
                ret['work_order'] = work_order
            return render(request, 'personal/order/order_storehouse_detail.html', ret)

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
        for order_status in Order.status_choices:
            status_dict = dict(item=order_status[0], value=order_status[1])
            status_list.append(status_dict)

        operation_manager = request.user.superior if request.user.superior else request.user
        ret = {
            'order': order,
            'status_list': status_list,
            'operation_manager': operation_manager,
            'type_list': type_list
        }
        return render(request, 'personal/workorder/workorder_update.html', ret)

    def post(self, request):
        res = dict()
        work_order = get_object_or_404(Order, pk=request.POST['id'])
        work_order_form = WorkOrderUpdateForm(request.POST, request.FILES, instance=work_order)
        if int(work_order.status) <= 1:
            if work_order_form.is_valid():
                work_order_form.save()
                res['status'] = 'success'
                if work_order.status == "2":
                    res['status'] = 'submit'
                    try:
                        SendMessage.send_workorder_email(request.POST['order_number'])
                        res['status'] = 'submit_send'
                    except Exception:
                        pass
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


class WorkOrderSendView(LoginRequiredMixin, View):
    """
        订单派发:运营经理完成 派发运营的订单给采购，
    """

    def get(self, request):
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
        res = dict(status='fail')
        work_order = get_object_or_404(Order, pk=request.POST['id'])
        work_order_record_form = OrderBugForm(request.POST, instance=work_order)
        if work_order_record_form.is_valid():
            if request.user.id == work_order.purchaser_id:
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


class WorkOrderFinishView(LoginRequiredMixin, View):

    def get(self, request):
        ret = dict()
        work_order = get_object_or_404(Order, pk=request.GET['id'])
        print(work_order.id)
        ret['order'] = work_order
        return render(request, 'personal/workorder/workorder_finish.html', ret)

    def post(self, request):
        res = dict(status='fail')
        work_order = get_object_or_404(Order, pk=request.POST['id'])
        work_order_record_form = OrderFinallyForm(request.POST, instance=work_order)
        if work_order_record_form.is_valid():
            if request.user.id == work_order.warehouse_staff_id and work_order.status != "5":
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
        #work_order_record = get_object_or_404(WorkOrderRecord, name_id=request.user.id, work_order_id=request.POST['id'])
        filters = dict(name_id=request.user.id, work_order_id=request.POST['id'])
        work_order_record = WorkOrderRecord.objects.filter(**filters).last()
        work_order_record_upload_form = WorkOrderRecordUploadForm(request.POST, request.FILES, instance=work_order_record)
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
