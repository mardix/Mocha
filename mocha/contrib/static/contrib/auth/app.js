
$(function() {
    $('#profile-photo-preview').imagepreview({
            input: '[id="profile-photo-input"]',
            preview: '#profile-photo-preview',
        });
    $("#btn-delete-profile-photo").click(function(){
        $("#profile-photo-preview").empty()
        $("#input-delete-photo").val("1")
    })
})
