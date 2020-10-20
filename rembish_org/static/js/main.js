!(function($) {
  "use strict";

  $(document).on('click', '.mobile-nav-toggle', function(e) {
    $('body').toggleClass('mobile-nav-active');
    $('.mobile-nav-toggle i').toggleClass('icofont-navigation-menu icofont-close');
  });

  $(document).click(function(e) {
    var container = $(".mobile-nav-toggle");
    if (!container.is(e.target) && container.has(e.target).length === 0) {
      if ($('body').hasClass('mobile-nav-active')) {
        $('body').removeClass('mobile-nav-active');
        $('.mobile-nav-toggle i').toggleClass('icofont-navigation-menu icofont-close');
      }
    }
  });

  // Hero typed
  if ($('.typed').length) {
    var typed_strings = $(".typed").data('typed-items');
    typed_strings = typed_strings.split(',')
    new Typed('.typed', {
      strings: typed_strings,
      loop: true,
      typeSpeed: 100,
      backSpeed: 50,
      backDelay: 2000
    });
  }

  $("#contact-form").submit(function(event) {
    event.preventDefault();
    const form = $(this);
    $("#submit", form).prop('disabled', true).hide();
    $(".loading", form).show();
    $(".validate", form).hide();

    $.ajax({
      type: form.attr("method"),
      url: form.attr("action"),
      data: form.serialize(),
      dataType: "json"
    }).done(function(data, textStatus, jqXHR) {
      $(".sent-message", form).show()
    }).fail(function(jqXHR, textStatus, errorThrown) {
      const errors = jqXHR.responseJSON.errors;
      Object.keys(errors).forEach(function(key) {
        $("#" + key, form).next().show().html(errors[key]);
      });
      $("#submit", form).prop('disabled', false).show();
    }).always(function() {
      $(".loading", form).hide();
    });
  });
})(jQuery);
