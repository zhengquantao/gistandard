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
from .models import WorkOrder, WorkOrderRecord, Order, StockOrder, MaternalSku
from .forms import WorkOrderCreateForm, WorkOrderUpdateForm, WorkOrderRecordForm, WorkOrderRecordUploadForm, \
    WorkOrderProjectUploadForm, OrderForm, OrderBackForm, OrderSendForm, OrderBugForm, OrderFinallyForm, \
    StockOrderCreateForm
from adm.models import Customer
from rbac.models import Role

from utils.toolkit import ToolKit, SendMessage
User = get_user_model()


class StockOrderView(LoginRequiredMixin, View):
    """
        工单视图：根据前端请求的URL 分为个视图：我创建的工单、我审批的工单和我收到的工单====
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        return render(request, 'personal/stockorder/stockorder.html', ret)


class StockOrderListView(LoginRequiredMixin, View):
    """
    工单列表：通过前端传递回来的url来区分不同视图，返回相应列表数据
    """
    def get(self, request):
        fields = ['id', 'system_sku', 'maternal_sku__sku', 'order_quantity', 'status', 'add_time', 'operation__name', 'operation_manager__name']
        filters = dict()
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
        ret = dict(data=list(StockOrder.objects.filter(**filters).values(*fields).order_by('-add_time')))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


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

        system_sku = request.POST.get("system_sku", "")
        maternal_sku = request.POST.get("maternal_sku", "")
        if system_sku or maternal_sku:
            # 库存
            order_quantity = request.POST.get("order_quantity", "")
            if not order_quantity:
                res['status'] = 'quantity_fail'
                return HttpResponse(json.dumps(res), content_type='application/json')
            stock_order.order_quantity = order_quantity

            # 状态
            status = request.POST.get("status", "")
            if not status:
                res['status'] = 'status_fail'
                return HttpResponse(json.dumps(res), content_type='application/json')
            stock_order.status = status

            # 审批人
            operation_manager = request.POST.get("operation_manager", "")
            if not operation_manager:
                res['operation_manager'] = 'operation_manager_fail'
                return HttpResponse(json.dumps(res), content_type='application/json')
            else:
                operation_manager_object = User.objects.filter(name=operation_manager).first()
                stock_order.operation_manager = operation_manager_object

            # 系统sku
            stock_order.system_sku = system_sku

            # 母体sku
            if maternal_sku:
                maternal_sku_object = MaternalSku.objects.filter(sku=maternal_sku).first()
                if maternal_sku_object:
                    stock_order.maternal_sku = maternal_sku_object
                else:
                    maternal_sku_object = MaternalSku(sku=maternal_sku)
                    stock_order.maternal_sku = maternal_sku_object

            # 申请人
            stock_order.operation = request.user
            stock_order.save()
            res['status'] = 'success'
            return HttpResponse(json.dumps(res), content_type='application/json')
        else:
            res['status'] = 'sku_fail'
            return HttpResponse(json.dumps(res), content_type='application/json')

