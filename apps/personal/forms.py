# @Time   : 2018/5/6 17:22
# @Author : RobbieHan
# @File   : forms.py


from django import forms
from django.contrib.auth import get_user_model

from .models import WorkOrder, WorkOrderRecord, Order

User = get_user_model()


class OrderForm(forms.ModelForm):
    """
    订单检查表
    """
    class Meta:
        model = Order
        fields = ["status", "order_number", "remark", "system_sku", "img", "product_chinese_name", "finish_status", "comparison_code", "purchase_quantity", "purchase_link", "operation", "operation_manager", "sales_30"]
        error_messages = {
            # "id": {"required": "请输入SKU"},
            "system_sku": {"required": "请输入SKU"},
            "order_number": {"required": "请输入订单号"},
            "status": {"required": "请输入状态"},
            "product_chinese_name": {"required": "请输入商品名"},
            "comparison_code": {"required": "请输入对照码"},
            "finish_status": {"required": "请输入品类"},
            "purchase_link": {"required": "请输入采购链接"},
            "sales_30": {"required": "请输入最近30天销量"},
            "purchase_quantity": {"required": "请输入订单数量"},
            "remark": {"required": "请输入备注内容"},
            "operation": {"required": "请选择提交人"},
            "operation_manager": {"required": "请选择审核人"},
        }


class OrderCreateForm(forms.ModelForm):
    """
    多余的
    """
    class Meta:
        model = Order
        fields = '__all__'


class OrderBackForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['remark1', 'id', 'status', 'operation_manager']


class OrderSendForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['id', 'status', 'remark1', 'purchaser']


class OrderBugForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['id', 'order_quantity', 'remark2', 'status']


class OrderFinallyForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['id', 'status', 'remark3', 'issued_quantity', 'remaining_stock_quantity', 'warehouse_staff']


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['image']


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'gender', 'birthday', 'email']


class WorkOrderCreateForm(forms.ModelForm):
    # approver = forms.(required=True, error_messages={"required": "请选择审批人"})
    class Meta:
        model = WorkOrder
        fields = '__all__'
        error_messages = {
            "title": {"required": "请输入工单标题"},
            "type": {"required": "请选择工单类型"},
            "status": {"required": "请选择工单状态"},
            "content": {"required": "请输入工单内容"},
        }

    def clean(self):
        cleaned_data = super(WorkOrderCreateForm, self).clean()
        approver = cleaned_data.get("approver", "")
        number = cleaned_data.get("number")
        if not approver:
            raise forms.ValidationError("请选择工单审批人")
        if WorkOrder.objects.filter(number=number).count():
            raise forms.ValidationError("工单编号已存在")


class WorkOrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["id", "status", "order_number", "remark", "system_sku", "img", "product_chinese_name", "finish_status", "comparison_code", "purchase_quantity", "purchase_link", "operation", "operation_manager", "sales_30"]
        error_messages = {
            "id": {"required": "请输入id"},
            "system_sku": {"required": "请输入SKU"},
            "order_number": {"required": "请输入订单号"},
            "status": {"required": "请输入状态"},
            "product_chinese_name": {"required": "请输入商品名"},
            "comparison_code": {"required": "请输入对照码"},
            "finish_status": {"required": "请输入品类"},
            "purchase_link": {"required": "请输入采购链接"},
            "sales_30": {"required": "请输入最近30天销量"},
            "purchase_quantity": {"required": "请输入订单数量"},
            "remark": {"required": "请输入备注内容"},
            "operation": {"required": "请选择提交人"},
            "operation_manager": {"required": "请选择审核人"},
        }

    def clean(self):
        cleaned_data = super(WorkOrderUpdateForm, self).clean()
        approver = cleaned_data.get("operation_manager", "")
        if not approver:
            raise forms.ValidationError("请选择工单审批人")


class WorkOrderRecordForm(forms.ModelForm):
    class Meta:
        model = WorkOrderRecord
        exclude = ['file_content', ]



class WorkOrderRecordUploadForm(forms.ModelForm):
    class Meta:
        model = WorkOrderRecord
        fields = ['file_content']


class WorkOrderProjectUploadForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = ['file_content']
