$("#commentForm").submit(function(e){
    e.preventDefault();
    let dt = new Date();
    let time = dt.getDay() + " " + monthNames[dt.getUTCMonth()] + ", " + dt.getFullYear();

    $.ajax({
        data: $(this).serialize(),
        method: $(this).attr("method"),
        url: $(this).attr("action"),
        dataType: "json",
        success: function(res){
            if(res.bool == true){
                $("#review-res").html("Review Added successfully");
                $(".hide-comment-form").hide();
                let _html = '<div class="single-comment justify-content-between d-left mb-30">';
				_html += '<div class="user justify-content-between d-lex">';
				_html += '<div class="thumb text-center">';
				_html += '<img src="">';
				_html += '<a href="" class="font-heading text-broad">'+ res.context.user +'</a>';
				_html += '</div>';
				_html += '<div class="desc">';
				_html += '<div class="d-flex justify-content-between mb-10">';
				_html += '<div class="d-flex align-items-center">';
				_html += '<span class="font-xs text-muted">'+ time +'</span>';
				_html += '</div>';
				for(let i = 1; i <= res.context.rating; i++){
                    _html += '<i class="fas fa-star text-warning"></i>';
                }
				_html += '</div>';
				_html += '<p class="mb-10">'+ res.context.review +'</p>';
				_html += '</div>';
				_html += '</div>';
				_html += '</div>';

                $(".comment-list").prepend(_html);
            }
        }
    });
});

$(".add-to-cart-btn-btn-btn").on("click", function(){
event.preventDefault(); // Ngăn chặn sự kiện click lan ra
    let this_val = $(this);
    let index = this_val.attr("data-index")

    let quantity = $(".product-quantity-" + index).val();
    let product_title = $(".product-title-" + index).val();

    let product_id = $(".product-id-" + index).val();
    let product_price = $("#product-price").val();

    let product_pid = $(".product-pid-" + index).val();
    let product_image = $(".product-image-" + index).val();


    console.log("quantity:", quantity);
    console.log("Title:", product_title);
    console.log("Price:", product_price);
    console.log("Id:", product_id);
    console.log("Pid:", product_pid);
    console.log("Image:", product_image);
    console.log("Index:", index);
    console.log("Current Element:", this_val);

    $.ajax({
        url: '/add-to-cart',
        data:{
            'id': product_id,
            'pid': product_pid,
            'image': product_image,
            'qty': quantity,
            'title': product_title,
            'price': product_price,
        },
        dataType: 'json',
        beforeSend: function(){
            console.log("Adding Product to cart...");
        },
        success: function(response){
            this_val.html("✔")
            console.log("Added Product to Cart!");
            $(".cart-items-count").text(response.totalcartitems)
        }
    })
})



});


//$(".add-to-cart-btn").on("click", function(){
//    let quantity = $("#product-quantity").val();
//    let product_title = $("#product-title").val(); // Sử dụng .text() để lấy nội dung của phần tử
//    let product_id = $("#product-id").val(); // Sử dụng .text() để lấy nội dung của phần tử
//    let product_price = $("#current-product-price").text();
//    let this_val = $(this);
//
//    console.log("quantity:", quantity);
//    console.log("Title:", product_title);
//    console.log("Price:", product_price);
//    console.log("Id:", product_id);
//    console.log("Current Element:", this_val);
//
//    $.ajax({
//        url: '/add-to-cart',
//        data:{
//            'id': product_id,
//            'qty': quantity,
//            'title': product_title,
//            'price': product_price,
//        },
//        dataType: 'json',
//        beforeSend: function(){
//            console.log("Adding Product to cart...");
//        },
//        success: function(response){
//            this_val.html("Item added to cart")
//            console.log("Added Product to Cart!");
//            $(".cart-items-count").text(response.totalcartitems)
//        }
//    })
//})

        var Tawk_API=Tawk_API||{}, Tawk_LoadStart=new Date();
			(function(){
			var s1=document.createElement("script"),s0=document.getElementsByTagName("script")[0];
			s1.async=true;
			s1.src='https://embed.tawk.to/5ac1aabb4b401e45400e4197/default';
			s1.charset='UTF-8';
			s1.setAttribute('crossorigin','*');
			s0.parentNode.insertBefore(s1,s0);
			})();

