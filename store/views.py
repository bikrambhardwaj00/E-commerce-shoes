from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .forms import RegistrationForm, AccountAuthenticationForm, CustomerForm, AddressForm, editbasicprofile
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, FormView, View, TemplateView
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models import Count
from .tasks import sleepy


def register(request):
    context ={}
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        profile_form = CustomerForm(request.POST)
        add_form = AddressForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            add = add_form.save(commit=False)
            add.user = user
            add.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            account = authenticate(username=username,password=raw_password)
            login(request,account)
            return HttpResponseRedirect('/home')
        else:
            context['registration_form'] = form
    else:
        form = RegistrationForm()
        profile_form = CustomerForm()
        add_form = AddressForm()
    context = {'registration_form':form, 'profile_form':profile_form , 'add_form':add_form}
    return render(request,'register.html',context)

def store(request):
    products = Product.objects.all()
    context = {'products':products}
    return render(request,'index.html',context)

@login_required(login_url="/login/")
def OrderSummaryView(request):   
    if request.user.is_authenticated:
        customer = request.user
        order = Order.objects.get(user=customer,ordered=False)
        items = order.items.all()
    else:
        items = []
        messages.warning(request, "You do not have an active order")
        return redirect("/")

    context = {'items':items, 'order':order}
    return render(request,'cart.html',context)

@login_required(login_url="/login/")
def checkout(request):
    if request.user.is_authenticated:
        customer = request.user
        order = Order.objects.get(user=customer,ordered=False)
        items = order.items.all()
    else:
        items = []
        order = {'get_cart_total':0, 'get_cart_items':0}
    context = {'items':items, 'order':order}
    return render(request,'checkout.html',context)

def login_view(request):
    context = {}
    user = request.user
    if user.is_authenticated:
        return HttpResponseRedirect('/home')
    if request.POST:
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username,password=password)
            if user:
                login(request,user)
                if request.GET.get('next', None):
                    return HttpResponseRedirect(request.GET['next'])
                return HttpResponseRedirect('/home')
    else:
        form = AccountAuthenticationForm()
    context['login_form'] = form
    return render(request,'login.html',context)

def logout_view(request):
    logout(request)
    return redirect('login')

class shopbybrand(ListView):
    model = Product
    template_name = "shopbybrand.html"
    # context_object_name = 'categories'
    def get_context_data(self, **kwargs):
        context = super(shopbybrand, self).get_context_data(**kwargs)
        brand_id = self.request.GET.get('category')
        total = Product.objects.values('brand').annotate(Count('brand'))
        
        context['total'] = total
        if brand_id:
            products = Product.get_product_by_category_id(brand_id)
            context['brands'] = products
            return context  
        else :            
            lst = Product.objects.values_list('brand', flat=True).order_by('brand').distinct()[:1]
            brand = Product.objects.filter(brand=lst)
            context['brands'] = brand
            return context
        return context

class Profile(TemplateView):
    model = Customer
    template_name = "profile.html"
    def get_queryset(self):
        return Customer.objects.filter(user=self.request.user)
    def get_context_data(self, **kwargs):
        context = super(Profile, self).get_context_data(**kwargs)
        context['users'] = self.get_queryset()
        return context

class Home(TemplateView):
    model = Product
    template_name = "index.html"
    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        context['products'] = Product.objects.order_by('-stock').filter()[:20]
        return context

def ProductDetailView(request,slug):
    product = Product.objects.get(slug=slug)
    context = {'product':product}
    return render(request,'product.html',context)
    
class SearchView(ListView):
    model = Product
    template_name = "search.html"

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        srch = self.request.GET.get('q')
        if srch:
            context['search'] = Product.objects.filter(Q(category__icontains=srch)|
                                                    Q(name__icontains=srch)|
                                                    Q(brand__icontains=srch))
            return context
        else:
            context['result'] = "No results found"

@login_required(login_url="/login/")
def add_to_cart(request, slug):
    item = get_object_or_404(Product, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        customer=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("cart")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("cart")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("cart")
    
@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Product, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                customer=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect("cart")
        else:
            context = {}
            messages.info(request, "This item was not in your cart")
            return redirect("product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")

@login_required
def remove_single_item_from_cart(request, slug):
    
    item = get_object_or_404(Product, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                customer=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            
            return redirect("cart")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("cart", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("cart", slug=slug)


def editprofile(request):
    if request.method == "POST":
        form = editbasicprofile(request.POST, instance=request.user)
        form1 = CustomerForm(request.POST,instance=request.user)
        form2 = AddressForm(request.POST,instance=request.user)

        if form.is_valid():
            user1 = form.save()
            mobile = form1.save(commit=False)
            mobile.user = user1
            mobile.save()
            return redirect('profile')
        # if form.is_valid() and form1.is_valid() and form2.is_valid():
        #     form.save()
        #     form1.save()
        #     form2.save()
        #     return redirect('profile')
    else:
        name = editbasicprofile(instance=request.user)
        mobile = Customer.objects.filter(user=request.user)
        address = ShippingAddress.objects.filter(user=request.user)
        context = {
            'name' : name,
            'mobile':mobile,
            'address':address,
            }
        return render(request,"editprofile.html",context)


def index(request):
    sleepy(10)
    return HttpResponse('<h1>TASK IS DONE</h1>')






