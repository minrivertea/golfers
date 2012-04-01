
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
	    }
	});
}


$(document).ready( function() {
	calculateShipping();
});
