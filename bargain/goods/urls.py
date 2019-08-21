from django.urls import path, re_path, include
from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter

from goods import views

router = DefaultRouter()
router.register('goods', views.GoodsAdminView)
router.register('goodsimage', views.GoodImageAdminView)
router.register('bargainrecord', views.BargainRecordAdminView)
router.register('orders', views.OrderGoodsAdminView)
router.register('user', views.UserAdminView)
router.register('activity1', views.ActivityAdminView)

urlpatterns = [
    path('register/',views.RegisterView.as_view({'post':'create'})),
    path('login/',views.Login.as_view()),
    path('activity/',views.GargainActivity.as_view({'get':'list'})),
    path('image/<int:id>/', views.GargainImage.as_view()),
    path('detail/<int:pk>/',views.GargainDetail.as_view({'get':'retrieve'})),
    path('order/',views.OrderViewSet.as_view({'post':'create'})),
    path('share/<int:pk>/',views.SharePoster.as_view({'get':'retrieve'})),
    path('friendsbargain/',views.FriendsBargain.as_view({'get':'retrieve'})),
    path('helpbargain/',views.HelpBargain.as_view({'get':'retrieve'})),
    path('mybargain/',views.MyBargain.as_view({'get':'retrieve'})),
    path('exchange/',views.ExchangeView.as_view({'get':'retrieve'})),
    path('wxshare/',views.ShowShareView.as_view({'get':'retrieve'})),
    path('exchangelist/',views.ExchangeList.as_view({'get':'list'})),
    path('exchangedetail/',views.ExchangeDetail.as_view({'get':'retrieve'})),
    path('hasexchange/<int:id>/',views.HasExchange.as_view()),
    path('uploadimage/',views.UploadImage.as_view()),
    path('pay/',views.Pay.as_view()),
    # path('pay_suc/',views.PaymentCenterRuiZ.as_view()),

    #管理页面接口
    path('', include(router.urls)),  # Router 方式


]