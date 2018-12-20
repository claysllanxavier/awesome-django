

function reload_inline_func() {
    // coloca a classe obrigatorio nos campos onde não tem ela, mas tem o attr required, a menos que seja do tipo checkbox, radio ou hidden
    $(':required:not(.obrigatorio):not([type="hidden"]):not([type="checkbox"]):not([type="file"])').each(function(){
         $(this).addClass('obrigatorio');
    });

    //    coloca o required nos inlines visiveis para fazer a validação
    $('.inline.dynamic-form:not(.formset-custom-template) .obrigatorio:not([required]):not([type="file"]):visible').each(function () {
        $(this).attr("required", "required");
    });

     // Aplicando regra CSS para o TD que tem um checkbox
    $("td:has(input[type='checkbox'])").css("float", "left").css("border", "none");
    // Ativando o plugin tooltip
    $('[data-toggle="tooltip"]').tooltip()

    // Aplicando mascara para os campo com class datefield
    $("input[class~='datefield']").inputmask({mask: '99/99/9999'});
    $("input[class~='datetimefield']").inputmask({mask: '99/99/9999 99:99'});
    $('.datepicker').datepicker({
        format: 'dd/mm/yyyy',
        autoclose: true,
        todayBtn: true,
        language: 'pt-BR'
    });

    $('input[type="file"]').on('change',function(){
        var fileName = this.files[0].name;
        $(this).siblings('.custom-file-label').html(fileName);
    });


    // não precisa mais pois é algo automatico do html5
    // $('.obrigatorio').each(function () {
    //     var field = this;
    //     if (field.checkValidity() == false) {
    //         $(field).siblings(".invalid-feedback").show();
    //         $(field).removeClass("valid");
    //     } else {
    //         $(field).siblings(".invalid-feedback").hide();
    //         $(field).addClass("valid");
    //     }
    // });
    // $(".obrigatorio").on('keyup', function () {
    //     var field = this;
    //     if (field.checkValidity() == false) {
    //         $(field).siblings(".invalid-feedback").show();
    //         $(field).removeClass("valid");
    //     } else {
    //         $(field).siblings(".invalid-feedback").hide();
    //         $(field).addClass("valid");
    //     }
    // });

    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.getElementsByClassName('needs-validation');
    // Loop over them and prevent submission
    var validation = Array.prototype.filter.call(forms, function (form) {
        form.addEventListener('submit', function (event) {
            if (form.checkValidity() === false) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
 }
// Example starter JavaScript for disabling form submissions if there are invalid fields
$(document).ready( function () {
    reload_inline_func();

    $( "a.add-row" ).on({
      click: function() {
           reload_inline_func();
      }
    });



    //funcionalidade para limpar as mensagens de alert apos um tempo definido
    // $(".alert").delay(15000).fadeTo(500, 0).slideUp(500, function() {
    //     $(this).alert('close');
    // });

    // funcionalidade utilizada no listview para limpar os filtros
    $('#id_clean_filter').on('click',function(){
        $('form#id_search_and_filter select').val("None").change();
        $('form#id_search_and_filter input' ).val("");
    });

     // funcionalidade utilizada nos filtro em caso de datas
    $('form#id_search_and_filter .dropdown-item').on('click',function(){
        id_input = $(this).attr("data-id-input");
        prefix = $(this).attr("data-prefix-filter");
        var input = $('#'+id_input);
        name_input = $(input).attr('name');
       if (name_input.includes('__')) {
           name_input = name_input.split("__")[0];
       }
       $(input).attr('name', name_input + prefix);
       $(this).siblings('div.active').removeClass('active');
       $(this).addClass('active');
    });

    // funcionalidade utilizada nos filtro em caso de datas
    $("form#id_search_and_filter .date-filter input[type='text']").each(function(){
        var prefix = "__"+$(this).attr('name').split("__")[1];
        var item = $(this).siblings("div .dropdown-menu").children('.dropdown-item[data-prefix-filter='+prefix+']');
        $(item).siblings('div.active').removeClass('active');
        $(item).addClass('active');
    });
});

