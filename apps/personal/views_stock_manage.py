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
from .forms import StockCreateForm, StockUpdateForm
from .models import Stock, Order
from rbac.models import Role
from utils.toolkit import ToolKit, SendMessage

User = get_user_model()


class StockView(LoginRequiredMixin, View):
    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        return render(request, 'personal/stock/stock.html', ret)


class StockListView(LoginRequiredMixin, View):
    def get(self, request):
        fields = ['id', 'system_sku', 'stock_quantity', 'maternal_sku__sku']
        filters = dict()
        sku = request.GET.get('number')
        if sku:
            filters['system_sku__icontains'] = sku
        ret = dict(data=list(Stock.objects.filter(stock_quantity__gt=0, **filters).values(*fields).order_by('-add_time')))
        print(ret, "===============")
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


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


class StockDetailView(LoginRequiredMixin, View):
    def get(self, request):
        pass


class StockDeleteView(LoginRequiredMixin, View):
    def post(self, request):
        ret = dict(result=False)
        if 'id' in request.POST and request.POST['id']:
            id_list = map(int, request.POST.get('id').split(','))
            Stock.objects.filter(id__in=id_list).delete()
            ret['result'] = True
        return HttpResponse(json.dumps(ret), content_type='application/json')


class StockUpdateView(LoginRequiredMixin, View):

    def get(self, request):
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
