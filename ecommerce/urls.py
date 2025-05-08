from django.contrib import admin
from django.urls import path, include
from store import views
from django.conf.urls.static import static
from django.conf import settings
# from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [

    path('admin/', admin.site.urls),
    path('', views.Home.as_view(), name='home'),

    path('checkout/',views.checkout,name="checkout"),
    path('login/',views.login_view,name="login"),
    path('shopbybrand/',views.shopbybrand.as_view(),name="shopbybrand"),
    path('register/',views.register,name="register"),
    path('logout/',views.logout_view,name="logout"),
    path('profile/',views.Profile.as_view(),name="profile"),
    path('home/',views.Home.as_view(),name="homeview"),
    path('product/<slug>/',views.ProductDetailView,name="product"),
    path('add-to-cart/<slug>/',views.add_to_cart,name="add-to-cart"),
    path('remove-from-cart/<slug>/',views.remove_from_cart,name="remove"),
    path('remove-single-item-from-cart/<slug>/',views.remove_single_item_from_cart,name="remove-single-item"),
    path('cart/', views.OrderSummaryView, name='cart'),
    path('profile/editprofile/', views.editprofile, name='editprofile'),
    path('search/',views.SearchView.as_view(),name="search"),
    # path('',views.index,name="index"),

    # path('editmobile/',views.editmobile.as_view(),name="editmobile"),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
