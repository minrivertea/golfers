
function calculateShipping() {
	$.ajax({
	    url: '{% url calculate_shipping order.id %}',
	    type: 'GET',
	    dataType: 'json',
	    success: function(data) {
	        $('#quotes').html(data.text);
	        $('#shipping-price').val(data.cost);
	        var currentTotal = parseFloat($("#total-cost").text());
	        var newTotal = parseFloat(currentTotal.toFixed(2)) + parseFloat(data.cost);
	        $('#total-cost').html(newTotal.toFixed(2));
	        $('#postage-loading').toggle();
	    },
        error: function() {
            $('form#paypal input[type=submit]').hide();
            $('#quotes').html("<p><strong>There's been a problem calculating shipping for the address you provided. You can <a href='/order/check-details/'>go back and check your address</a> (did you provide the full address including state, country and ZIP code?) or <a href='/contact-us/'>get in touch with us</a>.</strong></p>");
        }
	});
}


$(document).ready( function() {
	calculateShipping();
});
