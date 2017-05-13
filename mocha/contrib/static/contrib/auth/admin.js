
var adminOnModalShow = function(el, callback) {
    $(el).on("show.bs.modal").on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget) // Button that triggered the modal
        var modal = $(this)
        callback(button, modal)
    })
}

$(function(){


    // ROLES

    var modalEditRoles = $("#modal-edit-user-roles");
    if (modalEditRoles.length > 0) {
        adminOnModalShow(modalEditRoles, function(button, modal){
            if(button.data("action") == "create") {
                modal.find(".delete-btn").hide()
            } else {
                modal.find(".delete-btn").show()
            }

            modal.find("[name='id']").val(button.data("id"))
            modal.find("[name='name']").val(button.data("name"))
            modal.find("[name='level']").val(button.data("level"))
            modal.find("[name='action']").val("update")
        })

        modalEditRoles.find(".delete-btn").click(function(){
            if(confirm("Do you want to delete this role?")) {
                modalEditRoles.find("[name='action']").val("delete")
                modalEditRoles.find("form").first().submit()
            }
        })
    }


        // USER INFO
        var modalEU = $("#modal-edit-user")
        if (modalEU.length > 0) {
            // Will automatically fill the form
            var modalEU = $("#modal-edit-user")

            modalEU.find("button.delete-btn").click(function(){
                if(confirm("Do you want to DELETE this user's account ?")) {
                    modalEU.find("input[name='action']").val("delete")
                    modalEU.find("form").submit()
                }
            })
            modalEU.find("button.undelete-btn").click(function(){
                if(confirm("Do you want to UNDELETE this user's account ?")) {
                    modalEU.find("input[name='action']").val("undelete")
                    modalEU.find("form").submit()
                }
            })
            modalEU.find("button.deactivate-btn").click(function(){
                if(confirm("Do you want to DEACTIVATE this user's account ?")) {
                    modalEU.find("input[name='action']").val("deactivate")
                    modalEU.find("form").submit()
                }
            })
            modalEU.find("button.activate-btn").click(function(){
                if(confirm("Do you want to ACTIVATE this user's account ?")) {
                    modalEU.find("input[name='action']").val("activate")
                    modalEU.find("form").submit()
                }
            })

            $("#email-password-reset").click(function(){
                if (confirm("Do you want to send the password reset to the email ?")) {
                    modalEU.find("input[name='action']").val("email-reset-password")
                    modalEU.find("form").submit()
                }
            })


            $("#email-account-verification").click(function(){
                if (confirm("Do you want to send email verification ?")) {
                    modalEU.find("input[name='action']").val("email-account-verification")
                    modalEU.find("form").submit()
                }
            })

            $("#reset-secret-key").click(function(){
                if (confirm("Do you want to reset the account secret-key ?")) {
                    modalEU.find("input[name='action']").val("reset-secret-key")
                    modalEU.find("form").submit()
                }
            })

            $("#delete-profile-image").click(function(){
                if (confirm("Do you want to delete the profile picture")) {
                    modalEU.find("input[name='action']").val("delete-profile-image")
                    modalEU.find("form").submit()
                }
            })
        }

})