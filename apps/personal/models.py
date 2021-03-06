import datetime
from django.db import models

from django.contrib.auth import get_user_model

from adm.models import Customer

User = get_user_model()


class WorkOrder(models.Model):
    type_choices = (('0', '初次安装'), ('1', '售后现场'), ('2', '远程支持'), ('3', '售前支持'))
    status_choices = (('0', '工单已退回'), ('1', '新建-保存'), ('2', '提交-等待审批'), ('3', '已审批-等待执行'), ('4', '已执行-等待确认'), ('5', '工单已完成'))
    number = models.CharField(max_length=10, verbose_name='工单号')
    title = models.CharField(max_length=50, verbose_name='标题')
    type = models.CharField(max_length=10, choices=type_choices, default='0', verbose_name='工单类型')
    status = models.CharField(max_length=10, choices=status_choices, default='0', verbose_name='工单状态')
    do_time = models.DateTimeField(default='', verbose_name='安排时间')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    content = models.CharField(max_length=300, verbose_name='工单内容')
    file_content = models.FileField(upload_to='file/%Y/%m', blank=True, null=True, verbose_name='项目资料')
    customer = models.ForeignKey(Customer, verbose_name='客户信息')
    proposer = models.ForeignKey(User, related_name='proposer', blank=True, null=True, on_delete=models.SET_NULL, verbose_name='申请人')
    approver = models.ForeignKey(User, related_name='approver', blank=True, null=True, on_delete=models.SET_NULL, verbose_name='审批人')
    receiver = models.ForeignKey(User, related_name='receiver', blank=True, null=True, on_delete=models.SET_NULL, verbose_name='接单人')

    class Meta:
        verbose_name = '工单信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class WorkOrderRecord(models.Model):
    type_choices = (('0', '退回'), ('1', "派发"), ('2', "执行"), ('3', "确认"))
    name = models.ForeignKey(User, verbose_name=u"记录人")
    work_order = models.ForeignKey(WorkOrder, verbose_name=u"工单信息")
    record_type = models.CharField(max_length=10, choices=type_choices, verbose_name=u"记录类型")
    content = models.CharField(max_length=500, verbose_name=u"记录内容", default="")
    file_content = models.FileField(upload_to='file/%Y/%m', blank=True, null=True, verbose_name='实施文档')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name=u"记录时间")

    class Meta:
        verbose_name = u"执行记录"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.record_type


class MaternalSku(models.Model):
    sku = models.CharField(max_length=50, verbose_name='母体系统SKU')
    mater_name = models.CharField(max_length=128, verbose_name='母体中文名', null=True, default='', blank=True)
    child_sku = models.CharField(max_length=128, verbose_name='子SKU', null=True, default='', blank=True)
    number = models.IntegerField(null=True, default=0, blank=True, verbose_name='对应数量')
    position = models.CharField(max_length=500, verbose_name='货品位置', blank=True, null=True, default="")
    add_time = models.DateField(default=datetime.datetime.today, verbose_name='创建时间')
    child_name = models.CharField(max_length=128, verbose_name='子中文名', null=True, default='', blank=True)
    mater_img = models.ImageField(upload_to="image/%Y/%m", max_length=100, null=True, blank=True)
    child_img = models.ImageField(upload_to="image/%Y/%m", max_length=100, null=True, blank=True)
    content = models.CharField(max_length=128, verbose_name='备注', null=True, default='', blank=True)


class Order(models.Model):
    """
    运营订单
    """
    status_choices = (('0', '已退回订单'), ('1', '已保存-未提交'), ('2', '已提交-等待审批'), ('3', '已审批-等待采购'), ('4', '已采购-等待质检'), ('6', '已质检-等待打包'), ('5', '订单已完成'), ('7', '已质检-还需采购'), ('8', '已采购-暂时缺货'))
    finish_status_choices = (('0', '成品'), ('1', '配件'))
    system_sku = models.CharField(max_length=50, verbose_name='系统SKU')
    img = models.ImageField(upload_to="image/%Y/%m", max_length=100, null=True, blank=True)
    order_number = models.CharField(max_length=10, verbose_name='订单号')
    status = models.CharField(max_length=10, choices=status_choices, default='0', verbose_name='订单状态')
    product_chinese_name = models.CharField(max_length=500, verbose_name='产品中文名')
    comparison_code = models.CharField(max_length=20, verbose_name='对照码')
    finish_status = models.CharField(max_length=10, choices=finish_status_choices, default='0', verbose_name='是否成品')
    purchase_link = models.CharField(max_length=500, verbose_name='采购链接')
    remaining_stock_quantity = models.IntegerField(verbose_name='剩余库存数量', null=True, blank=True)
    issued_quantity = models.IntegerField(verbose_name='已发出数量', null=True, blank=True)
    sales_30 = models.CharField(max_length=50, verbose_name='最近30天销量', null=True)
    order_quantity = models.IntegerField(verbose_name='采购下单数量', null=True, blank=True)
    purchase_quantity = models.IntegerField(verbose_name='运营采购数量', blank=True, null=True)
    add_time = models.DateField(default=datetime.datetime.today, verbose_name='创建时间')
    remark = models.CharField(max_length=500, verbose_name="运营备注", null=True, blank=True)
    remark1 = models.CharField(max_length=500, verbose_name="运营经理备注", null=True, blank=True)
    remark2 = models.CharField(max_length=500, verbose_name="采购备注", null=True, blank=True)
    remark3 = models.CharField(max_length=500, verbose_name="仓库备注", null=True, blank=True)
    remark4 = models.CharField(max_length=500, verbose_name="质检备注", null=True, blank=True)
    time2 = models.DateTimeField(verbose_name="运营经理确认时间", default=datetime.datetime.today, null="", blank=True)
    time3 = models.DateTimeField(verbose_name="采购确认时间", default=datetime.datetime.today, null="", blank=True)
    time4 = models.DateTimeField(verbose_name="质检确认时间", default=datetime.datetime.today, null="", blank=True)
    time5 = models.DateTimeField(verbose_name="打包确认时间", default=datetime.datetime.today, null="", blank=True)
    maternal_sku = models.ForeignKey(MaternalSku, related_name="maternal_sku", blank=True, null=True, on_delete=models.SET_NULL, verbose_name='母体SKU')
    operation = models.ForeignKey(User, related_name='operation', blank=True, null=True, on_delete=models.SET_NULL, verbose_name='运营')
    operation_manager = models.ForeignKey(User, related_name='operation_manager', null=True, on_delete=models.SET_NULL, verbose_name='运营经理')
    purchaser = models.ForeignKey(User, related_name='purchaser', blank=True, null=True, on_delete=models.SET_NULL, verbose_name='采购人员')
    warehouse_staff = models.ForeignKey(User, related_name='warehouse_staff', blank=True, null=True, on_delete=models.SET_NULL, verbose_name='仓储人员')
    purchase_status = models.IntegerField(verbose_name="采购状态", default=0, null=True, blank=True)
    position = models.CharField(max_length=500, verbose_name='质检位置', blank=True, null=True, default="")
    lack = models.IntegerField(verbose_name="打包缺少数量", null=True, blank=True, default=0)
    lack_warehouse_staff = models.IntegerField(verbose_name='质检缺或坏数量', null=True, blank=True, default=0)
    store_choices = (('0', '未缺货'), ('1', '缺货'))
    is_store = models.CharField(max_length=5, choices=store_choices, default='0', verbose_name='是否入库')
    lack_purchase = models.IntegerField(verbose_name='采购缺的数量', null=True, blank=True, default=0)
    fba_store = models.IntegerField(verbose_name='FBA库存数', null=True, blank=True, default=0)
    load_num = models.IntegerField(verbose_name='在路上的数量', null=True, blank=True, default=0)
    read_choices = (('0', '未读'), ('1', '已读'))
    is_read = models.CharField(max_length=5, choices=read_choices, default='0', verbose_name='是否已读')


class OrderManager(models.Model):
    """
    运营经理
    """
    # status_choices = (('0', '已提交-等待审批'), ('1', '已审批-等待采购'))
    # finish_status_choices = (('0', '成品'), ('1', '配件'))
    # system_sku = models.CharField(max_length=50, verbose_name='系统SKU')
    # img = models.ImageField(upload_to="image/%Y/%m", max_length=100, null=True, blank=True)
    # order_number = models.CharField(max_length=10, verbose_name='订单号')
    # status = models.CharField(max_length=10, choices=status_choices, default='0', verbose_name='订单状态')
    # product_chinese_name = models.CharField(max_length=500, verbose_name='产品中文名')
    # comparison_code = models.CharField(max_length=20, verbose_name='对照码')
    # finish_status = models.CharField(max_length=10, choices=finish_status_choices, default='0', verbose_name='是否成品')
    # sales_30 = models.CharField(max_length=50, verbose_name='最近30天销量', null=True)
    # purchase_quantity = models.IntegerField(verbose_name='运营采购数量', blank=True, null=True)
    # add_time = models.DateField(default=datetime.datetime.today, verbose_name='创建时间')
    # remark = models.CharField(max_length=500, verbose_name="运营备注", null=True, blank=True)
    # remark1 = models.CharField(max_length=500, verbose_name="运营经理备注", null=True, blank=True)
    # time2 = models.DateTimeField(verbose_name="运营经理确认时间", default=datetime.datetime.today, null="", blank=True)
    # maternal_sku = models.ForeignKey(MaternalSku, related_name="maternal_sku", blank=True, null=True,
    #                                  on_delete=models.SET_NULL, verbose_name='母体SKU')
    # operation = models.ForeignKey(User, related_name='operation', blank=True, null=True, on_delete=models.SET_NULL,
    #                               verbose_name='运营')
    # operation_manager = models.ForeignKey(User, related_name='operation_manager', null=True, on_delete=models.SET_NULL,
    #                                       verbose_name='运营经理')
    # fba_store = models.IntegerField(verbose_name='FBA库存数', null=True, blank=True, default=0)
    # load_num = models.IntegerField(verbose_name='在路上的数量', null=True, blank=True, default=0)
    # read_choices = (('0', '未读'), ('1', '已读'))
    # is_read = models.CharField(max_length=5, choices=read_choices, default='0', verbose_name='是否已读')


class OrderBug(models.Model):
    """
    采购订单
    """
    pass


class OrderCheck(models.Model):
    """
    质检订单
    """
    pass


class OrderPack(models.Model):
    """
    打包订单
    """
    pass

class Stock(models.Model):
    status_choices = (
        ('0', '订单已退回'), ('1', '新建-保存'), ('2', '提交-等待审批'), ('3', '已审批-等待采购'), ('4', '已采购-等待确认'), ('5', '订单已完成'))
    finish_status_choices = (('0', '成品'), ('1', '配件'))
    system_sku = models.CharField(max_length=50, verbose_name='系统SKU', blank=True, null=True)
    img = models.ImageField(upload_to="image/%Y/%m", max_length=100, null=True, blank=True,
                            default="image/default2.png")
    order_number = models.CharField(max_length=10, verbose_name='订单号', blank=True, null=True)
    status = models.CharField(max_length=10, choices=status_choices, default='0', verbose_name='订单状态')
    product_chinese_name = models.CharField(max_length=500, verbose_name='产品中文名', blank=True, null=True)
    comparison_code = models.CharField(max_length=20, verbose_name='对照码', blank=True, null=True)
    finish_status = models.CharField(max_length=10, choices=finish_status_choices, default='0', verbose_name='是否成品')
    purchase_link = models.CharField(max_length=500, verbose_name='采购链接', blank=True, null=True)
    stock_quantity = models.IntegerField(verbose_name='剩余库存数量', null=True, blank=True)
    add_time = models.DateField(default=datetime.datetime.today, verbose_name='创建时间')
    maternal_sku = models.ForeignKey(MaternalSku, related_name="stock_maternal_sku", blank=True, null=True,
                                     on_delete=models.SET_NULL, verbose_name='母体SKU')
    position = models.CharField(max_length=500, verbose_name='位置', blank=True, null=True, default="")
    accessories_name = models.CharField(max_length=50, verbose_name='配件名称', blank=True, null=True, default="")
    remark = models.CharField(max_length=500, verbose_name='备注', blank=True, null=True, default="")


class StockOrder(models.Model):
    status_choices = (('0', '订单已退回'), ('1', '新建-保存'), ('2', '提交-等待审批'), ('3', '已审批-订单完成'))
    system_sku = models.CharField(max_length=50, verbose_name='系统SKU', blank=True, null=True)
    maternal_sku = models.ForeignKey(MaternalSku, related_name="stock_order_maternal_sku", blank=True, null=True, on_delete=models.SET_NULL, verbose_name='母体SKU')
    order_quantity = models.IntegerField(verbose_name='下单数量', null=True)
    status = models.CharField(max_length=10, choices=status_choices, default='0', verbose_name='订单状态')
    add_time = models.DateField(default=datetime.datetime.today, verbose_name='添加时间')
    operation = models.ForeignKey(User, related_name='stock_order_operation', null=True, on_delete=models.SET_NULL, verbose_name='运营')
    operation_manager = models.ForeignKey(User, related_name='stock_order_operation_manager', null=True, on_delete=models.SET_NULL, verbose_name='运营经理')


class SkuToUrl(models.Model):
    """
    sku对应URL表
    """
    status_choices = (('0', '不常用'), ('1', '常用'))
    sku = models.CharField(max_length=120, verbose_name="商品sku", null=True, default="")
    url = models.CharField(max_length=256, verbose_name="商品url", null=True, default="")
    supplier = models.CharField(max_length=120, verbose_name="供应商名称", null=True, default="")
    status = models.CharField(max_length=10, choices=status_choices, default='0', verbose_name='是否常用')


class PersonStore(models.Model):
    """
    个人库存清算
    """
    system_sku = models.CharField(max_length=120, verbose_name="商品sku", null=True, default="")
    product_chinese_name = models.CharField(max_length=120, verbose_name="中文名", null=True, default="")
    img = models.CharField(max_length=256, verbose_name="图片", null=True, default="")
    number = models.IntegerField(verbose_name="当前数量", null=True, default=0)
    time = models.DateField(default=datetime.datetime.today, verbose_name='添加时间')
    other = models.CharField(max_length=256, verbose_name="备用字段位置", null=True, default=0)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='所属人')


class StockLog(models.Model):
    """
    库存操作日志
    """
    user = models.CharField(max_length=60, verbose_name="操作人", null=True, default="")
    after_number = models.IntegerField(verbose_name="操作后数量", null=True, default="")
    before_number = models.IntegerField(verbose_name="操作前数量", null=True, default="")
    time = models.DateTimeField(verbose_name="操作时间", auto_now_add=True, auto_created=True)
    content = models.CharField(verbose_name="操作内容", max_length=60, null=True, default="")
    sku = models.CharField(verbose_name="商品sku", max_length=60, null=True, default="")
    sku_name = models.CharField(verbose_name="中文名", max_length=60, null=True, default="")