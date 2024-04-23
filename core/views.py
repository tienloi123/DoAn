from django.http import  JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string

from core.models import Product, Category, Vendor, CartOrder, ProductImages, ProductReview, wishlist_model, \
    Address, CartOrderItems, Coupon
from core.forms import ProductReviewForm
from django.db.models import Count, Avg
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
import cv2
import numpy as np
from django.core import serializers
import  calendar
from django.db.models.functions import ExtractMonth

from userauths.models import Profile, User


# Create your views here.


def intro(request):
    return render(request, 'core/intro.html')


def index(request):
    products = Product.objects.filter(product_status="published", featured=True)

    context = {
        "products": products
    }

    return render(request, 'core/index.html', context)


def product_list_view(request):
    products = Product.objects.filter(product_status="published")

    context = {
        "products": products
    }

    return render(request, 'core/product-list.html', context)


def category_list_view(request):
    categories = Category.objects.all().annotate(product_count=Count("category"))

    context = {
        "categories": categories
    }
    return render(request, 'core/category-list.html', context)


def category_product_list_view(request, cid):
    category = Category.objects.get(cid=cid)
    products = Product.objects.filter(product_status="published", category=category)

    context = {
        "category": category,
        "products": products,
    }
    return render(request, 'core/category-product-list.html', context)


def vendor_list_view(request):
    vendor = Vendor.objects.all()
    context = {
        "vendor": vendor,
    }
    return render(request, "core/vendor-list.html", context)


def products(request):
    return render(request, 'core/product-list.html')


def product_detail_view(request, pid):
    product = Product.objects.get(pid=pid)
    products = Product.objects.filter(category=product.category).exclude(pid=pid)

    reviews = ProductReview.objects.filter(product=product).order_by("-date")
    average_rating = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))
    # Làm tròn đến một chữ số thập phân
    average_rating = round(average_rating['rating'], 1) if average_rating['rating'] else 0
    review_form = ProductReviewForm()
    make_review = True
    if request.user.is_authenticated:
        user_review_count = ProductReview.objects.filter(user=request.user, product=product).count()
        if user_review_count > 0:
            make_review = False
    p_image = product.p_images.all()

    context = {
        "p": product,
        "review_form": review_form,
        "p_image": p_image,
        "make_review": make_review,
        "average_rating": average_rating,
        "reviews": reviews,
        "products": products,
    }
    return render(request, "core/product-detail.html", context)

def ajax_add_review(request, pid):
    product = Product.objects.get(pk=pid)
    user = request.user

    review = ProductReview.objects.create(
        user=user,
        product=product,
        review=request.POST['review'],
        rating=request.POST['rating'],
    )

    context = {
        'user': user.username,
        'review': request.POST['review'],
        'rating': request.POST['rating'],
    }
    average_reviews = ProductReview.objects.filter(product=product).aggregate(rating=Avg("rating"))

    return JsonResponse(
        {
            'bool': True,
            'context': context,
            'average_reviews': average_reviews
        }
    )
def add_to_cart(request):
    cart_product = {}

    cart_product[str(request.GET['id'])] = {
        'title': request.GET['title'],
        'qty': request.GET['qty'],
        'price': request.GET['price'],
        'image': request.GET['image'],
        'pid': request.GET['pid'],
        'stock': request.GET['stock'],
    }

    if 'cart_data_obj' in request.session:
        if str(request.GET['id']) in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = int(cart_product[str(request.GET['id'])]['qty'])
            cart_data.update(cart_data)
            request.session['cart_data_obj'] = cart_data
        else:
            cart_data = request.session['cart_data_obj']
            cart_data.update(cart_product)
            request.session['cart_data_obj'] = cart_data
    else:
        request.session['cart_data_obj'] = cart_product
    return JsonResponse({"data":request.session['cart_data_obj'],'totalcartitems':len(request.session['cart_data_obj'])})

def cart_view(request):
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
                cart_total_amount += int(item['qty']) * float(item['price'])

        user = User.objects.filter(username=request.user).first()
        profile = Profile.objects.filter(user_id=user.id).first()
        address = Address.objects.filter(user_id=user.id, status=True).first()
        return render(request, "core/cart.html", {"cart_data":request.session['cart_data_obj'],'totalcartitems':len(request.session['cart_data_obj']), 'cart_total_amount': cart_total_amount, "profile": profile, "address": address})
    else:
        return redirect("core:index")

def delete_item_from_cart(request):
    product_id = str(request.GET['id'])
    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            del request.session['cart_data_obj'][product_id]
            request.session['cart_data_obj'] = cart_data

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {"cart_data":request.session['cart_data_obj'],'totalcartitems':len(request.session['cart_data_obj']), 'cart_total_amount': cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems':len(request.session['cart_data_obj'])})

def update_cart(request):
    product_id = str(request.GET['id'])
    product_qty = request.GET['qty']

    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = product_qty
            request.session['cart_data_obj'] = cart_data

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {"cart_data":request.session['cart_data_obj'],'totalcartitems':len(request.session['cart_data_obj']), 'cart_total_amount': cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems':len(request.session['cart_data_obj'])})



def payment_completed_view(request, oid):
    order = CartOrder.objects.get(oid=oid)
    if order.paid_status == False:
        order.paid_status = True
        order.save()

    context = {
        "order": order,
    }
    return render(request, "core/payment-completed.html", context)


def payment_failed_view(request):
    return render(request, 'core/payment-failed.html')


def customer_dashboard(request):
    orders_list = CartOrder.objects.filter(user=request.user).order_by("-id")
    address = Address.objects.filter(user=request.user)

    profile = Profile.objects.get(user=request.user)

    orders = CartOrder.objects.annotate(month=ExtractMonth("order_date")).values("month").annotate(count=Count("id")).values("month", "count")
    month = []
    total_orders = []

    for i in orders:
        month.append(calendar.month_name[i["month"]])
        total_orders.append(i["count"])


    if request.method == "POST":
        address = request.POST.get("address")
        mobile = request.POST.get("mobile")

        new_address = Address.objects.create(
            user = request.user,
            address = address,
            mobile = mobile,
        )
        return redirect("core:dashboard")
    context = {
        "orders": orders,
        "profile": profile,
        "orders_list": orders_list,
        "address": address,
        "month": month,
        "total_orders": total_orders,
    }
    return render(request, 'core/dashboard.html', context)
def order_detail(request, id):
    order = CartOrder.objects.get(user=request.user,id = id)
    order_items = CartOrderItems.objects.filter(order = order)

    context = {
        "order_items": order_items,
    }
    return render(request, 'core/order-detail.html',context)

def make_address_default(request):
    id = request.GET['id']
    Address.objects.update(status=False)
    Address.objects.filter(id=id).update(status=True)
    return JsonResponse({"boolean": True})


def add_to_wishlist(request):
    product_id = request.GET['id']
    product = Product.objects.get(id=product_id)

    context = {}
    wishlist_count = wishlist_model.objects.filter(product=product, user = request.user).count()
    print(wishlist_count)

    if wishlist_count>0:
        context = {
            "bool": True
        }
    else:
        new_wishlist = wishlist_model.objects.create(
            user=request.user,
            product = product,
        )
        context = {
            "bool": True
        }
    return JsonResponse(context)
def wishlist_view(request):
    try:
        wishlist = wishlist_model.objects.all()
    except:
        wishlist=None

    context = {
        "w":wishlist
    }
    return render(request, "core/wishlist.html", context)

def remove_wishlist(request):
    try:
        pid = request.GET['id']
        wishlist = wishlist_model.objects.filter(user=request.user)
        product = wishlist_model.objects.get(id=pid)
        product.delete()

        # Serialize wishlist queryset to JSON
        wishlist_json = serializers.serialize('json', wishlist)

        # Render wishlist HTML asynchronously
        wishlist_html = render_to_string("core/async/wishlist-list.html", {"w": wishlist})

        # Return JSON response with updated wishlist HTML and JSON data
        return JsonResponse({"data": wishlist_html, "w": wishlist_json})
    except Exception as e:
        return JsonResponse({"error": str(e)})

def checkout(request, oid):
    order = CartOrder.objects.get(oid=oid)
    order_items = CartOrderItems.objects.filter(order=order)

    if request.method == "POST":
        code = request.POST.get("code")
        coupon = Coupon.objects.filter(code=code, active=True).first()
        if coupon:
            if coupon in order.coupons.all():
                return redirect("core:checkout", order.oid)
            else:
                discount = order.price * coupon.discount / 100
                order.coupons.add(coupon)
                order.price -= discount
                order.saved += discount
                order.save()

                return redirect("core:checkout", order.oid)
        else:
            messages.warning(request, "Coupon does not exist")
            return redirect("core:checkout", order.oid)


    context = {
        "order": order,
        "order_items": order_items,
    }

    return render(request, "core/checkout.html", context)
def save_checkout_info(request):
    cart_total_amount = 0
    total_amount = 0

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        country = request.POST.get("country")
        pid = request.POST.get("pid")

        request.session['full_name'] = full_name
        request.session['email'] = email
        request.session['mobile'] = mobile
        request.session['address'] = address
        request.session['city'] = city
        request.session['state'] = state
        request.session['country'] = country

        if 'cart_data_obj' in request.session:
            # Tính tổng số tiền cho đơn hàng
            for p_id, item in request.session['cart_data_obj'].items():
                total_amount += int(item['qty']) * float(item['price'])

            # Tạo đơn hàng mới và lưu vào cơ sở dữ liệu
            order = CartOrder.objects.create(
                user=request.user,
                price=total_amount,
                full_name=full_name,
                email=email,
                phone=mobile,
                address=address,
                city=city,
                state=state,
                country=country,
            )

            del request.session['full_name']
            del request.session['email']
            del request.session['mobile']
            del request.session['address']
            del request.session['city']
            del request.session['state']
            del request.session['country']


            # Lưu thông tin sản phẩm trong giỏ hàng vào cơ sở dữ liệu
            for p_id, item in request.session['cart_data_obj'].items():
                cart_order_products = CartOrderItems.objects.create(
                    order=order,
                    invoice_no="INVOICE_NO" + str(order.id),
                    item=item['title'],
                    image=item['image'],
                    qty=item['qty'],
                    price=item['price'],
                    total=float(item['qty']) * float(item['price'])
                )
                # Cập nhật số lượng hàng tồn kho của sản phẩm
                product = Product.objects.get(pid=pid)
                product.stock_count = int(product.stock_count) - int(item['qty'])
               # product.stock_count -= int(item['qty'])  # Giảm số lượng tồn kho
                product.save()  # Lưu lại thông tin sản phẩm

            # Xóa giỏ hàng sau khi đã đặt hàng thành công
            del request.session['cart_data_obj']
        return redirect("core:checkout", order.oid)
    return redirect("core:checkout", order.oid)

def order_placed_view(request):
    return render(request, 'core/order_placed.html')

def glass_try(request):

    # Load model
    face_detection_model = cv2.CascadeClassifier("models/haarcascade_frontalface_alt.xml")
    eye_detection_model = cv2.CascadeClassifier("models/haarcascade_eye.xml")

    product_image = request.GET.get('glass_image_path', None)
    chuoi_moi = product_image[1:]
    glass_image = cv2.imread(chuoi_moi)
    vid = cv2.VideoCapture(0)
    while True:
        ret, image = vid.read()
        if ret:

            final_image = image
            # 1. Phát hiện khuôn mặt
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            faces = face_detection_model.detectMultiScale(gray_image, scaleFactor=1.3, minNeighbors=5, minSize=(200,200))

            if len(faces) > 0:

                for (face_x, face_y, face_w, face_h) in faces:

                    # 2. Phát hiện mắt
                    eye_centers = []
                    face_roi = gray_image[face_y: face_y + face_h, face_x : face_x + face_w]

                    eyes = eye_detection_model.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=5, minSize=(100,100))

                    # Lấy tâm của 2 mắt
                    for (eye_x, eye_y, eye_w, eye_h) in eyes:
                        eye_centers.append((face_x + int(eye_x + eye_w/2), face_y + int(eye_y + eye_h/2)))

                    if len(eye_centers) >=2:

                        # Tính toán toạ độ và kích thước của kính
                        glass_width_resize = 2.5 * abs(eye_centers[1][0] - eye_centers[0][0])
                        scale_factor = glass_width_resize / glass_image.shape[1]

                        # Làm tròn kích thước mới của resize_glasses để đảm bảo rằng nó là số nguyên
                        resize_glasses = cv2.resize(glass_image, None, fx= scale_factor, fy=scale_factor)

                        # Tính toạ đọ của kính
                        if eye_centers[0][0] <  eye_centers[1][0]:
                            left_eye_x = eye_centers[0][0]
                        else:
                            left_eye_x = eye_centers[1][0]

                        glass_x = left_eye_x - 0.28 * resize_glasses.shape[1]
                        glass_y = face_y + 0.8 * resize_glasses.shape[0]

                        # 4. Vẽ kính lên mặt

                        overlay_image = np.ones(image.shape, np.uint8)  * 255
                        overlay_image[int(glass_y): int(glass_y + resize_glasses.shape[0]),
                                      int(glass_x): int(glass_x + resize_glasses.shape[1])] = resize_glasses

                        gray_overlay = cv2.cvtColor(overlay_image, cv2.COLOR_BGR2GRAY)
                        _, mask = cv2.threshold(gray_overlay, 127, 255, cv2.THRESH_BINARY)

                        # Lấy phần background và face (trừ phần kính mắt) ra khỏi ảnh gốc
                        background = cv2.bitwise_and(image, image, mask = mask)

                        mask_inv = cv2.bitwise_not(mask)

                        # Lấy phần kính ra khỏi overlay
                        glasses = cv2.bitwise_and(overlay_image, overlay_image, mask=mask_inv)

                        final_image = cv2.add(background, glasses)

            cv2.imshow("Model", final_image)

        if cv2.waitKey(1) == ord('q'):
            break

    cv2.destroyAllWindows()
def search_view(request):
    query = request.GET.get("p")
    products = []
    if query:
        products = Product.objects.filter(title__icontains=query).order_by("-date")
    context = {
        "products": products,
        "query": query,
    }
    return render(request, "core/search.html", context)
def filter_product(request):
    categories = request.GET.getlist("category[]")
    vendors = request.GET.getlist("vendor[]")

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Product.objects.filter(product_status="published").order_by("-id").distinct()
    # if min_price and max_price:
    #     products = products.filter(price__gte=min_price, price__lte=max_price)
    products = products.filter(price__gte=min_price)
    products = products.filter(price__lte=max_price)
    if len (categories) > 0:
        products = products.filter(category__id__in=categories).distinct()
    if len (vendors) > 0:
        products = products.filter(vendor__id__in=vendors).distinct()

    # Render the product list template with the filtered products
    data = render_to_string("core/async/product-list.html", {"products": products})

    # Return the rendered product list HTML as JSON response
    return JsonResponse({"data": data})
