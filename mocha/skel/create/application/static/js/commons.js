// Commons.js

$(function(){
    
    // Form validator
    $.validate({
        modules : 'security'
    });
    
    // Datetime picker
    $('.datetimepicker').datetimepicker({
            debug: true,
            icons: {
                time: 'fa fa-clock-o',
                date: 'fa fa-calendar',
                up: 'fa fa-chevron-up',
                down: 'fa fa-chevron-down',
                previous: 'fa fa-chevron-left',
                next: 'fa fa-chevron-right',
                today: 'fa fa-screenshot',
                clear: 'fa fa-trash',
                close: 'fa fa-remove'
            }
    });

    // Lazy load images
    $("img.lazy").lazy({
        effect: "fadeIn",
        effectTime: 500
    })

    // Oembed
    $("a.oembed").oembed(null, {
        includeHandle: false,
        maxWidth: "100%",
        maxHeight: "480",
    });
    
})
