const inputs = document.querySelectorAll('.input');
const flashNodes = document.querySelectorAll('.flash');
const species = document.querySelectorAll('.species');
const visibleChoose = document.querySelectorAll(".visible-checkbox");
const selected = document.querySelectorAll(".selected");
const areas = document.querySelectorAll("textarea");

areas.forEach(area => {
    area.addEventListener('input', () => {
        area.parentNode.parentNode.style.height = "";
        area.parentNode.parentNode.style.height = area.scrollHeight + "px";
    });
    area.parentNode.parentNode.style.height = "";
    area.parentNode.parentNode.style.height = area.scrollHeight + "px";
});


visibleChoose.forEach(visible => {
    visible.addEventListener("click", () => {
        if(confirm('Wenn sie ihr Profil sichtbar machen, kann jeder ihren Benutzernamen und ihre E-Mail Adresse, sowie eine übersicht über ihre Aktivitäten auf dieser Internetseite sehen! Diese Aktion kann jederzeit rückgängig gemacht werden!')) {
            let parent = visible.parentNode.parentNode;
            open = parent.querySelector(".fa-eye");
            slash = parent.querySelector(".fa-eye-slash");
            label = parent.querySelector(".visible-text");



            if(visible.checked) {
                label.innerHTML = "Ihr Profil ist sichtbar";

                if(slash !== null) {
                    slash.classList.toggle("fa-eye");
                    slash.classList.remove("fa-eye-slash");
                }
            } else {
                label.innerHTML = "Ihr Profil ist unsichtbar";

                if(open !== null) {
                    open.classList.remove("fa-eye");
                    open.classList.toggle("fa-eye-slash");
                }
            }
        }
    });
});

selected.forEach(select => {
    arrow = select.parentNode.parentNode.parentNode.querySelector('.arrow');
    if(arrow !== null) {
        arrow.addEventListener("click", () => {
            optionContainer = select.parentNode.querySelector(".option-container");
            optionContainer.classList.toggle("active");
            arrowDown = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-down");
            arrowUp = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-up");
            if(arrowDown !== null) {
                arrowDown.classList.remove("fa-angle-down");
                arrowDown.classList.toggle("fa-angle-up");
            }

            if(arrowUp !== null) {
                arrowUp.classList.toggle("fa-angle-down");
                arrowUp.classList.remove("fa-angle-up");
            }
        });
    }

    select.addEventListener("click", () => {
        optionContainer = select.parentNode.querySelector(".option-container");
        optionContainer.classList.toggle("active");
        arrowDown = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-down");
        arrowUp = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-up");
        if(arrowDown !== null) {
            arrowDown.classList.remove("fa-angle-down");
            arrowDown.classList.toggle("fa-angle-up");
        }

        if(arrowUp !== null) {
            arrowUp.classList.toggle("fa-angle-down");
            arrowUp.classList.remove("fa-angle-up");
        }
    });
    optionsList = select.parentNode.querySelectorAll(".option");
    optionsList.forEach( o => {
        o.addEventListener("click", () => {
            select.value = o.querySelector("label").innerHTML;
            optionContainer = select.parentNode.querySelector(".option-container");
            optionContainer.classList.remove("active");
            header = select.parentNode.parentNode.querySelector('.selection-header');
            if(header !== null) {
                header.classList.add('active');
            }
            arrowUp = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-up");
            if(arrowUp !== null) {
                arrowUp.classList.toggle("fa-angle-down");
                arrowUp.classList.remove("fa-angle-up");
            }
        });
    });
    searchBox = select.parentNode.querySelector(".search-box input");
    searchBox.addEventListener("keyup", function(e) {
        var input = e.target;
        var filter = input.value.toUpperCase();
        var options = select.parentNode.querySelectorAll('.option label');
        var i;
        for(i = 0; i < options.length; i++) {
            topic = options[i];

            if(topic.innerHTML.toUpperCase().indexOf(filter)>-1) {
                options[i].parentNode.style.display = "";
            } else {
                options[i].parentNode.style.display = "none";
            }
        }
    });


    let parent = select.parentNode.parentNode.parentNode;

    if(parent.querySelector('.second') == null && select.value !== null && select.value !== '') {
        parent.classList.add('focus');
    }
});

function focusFunc() {
    let parent = this.parentNode.parentNode;
    parent.classList.add('focus');
}

function blurFunc() {
    let parent = this.parentNode.parentNode;
    if(this.value == "") {
        parent.classList.remove('focus');
    }
}

inputs.forEach(input => {
    input.addEventListener('focus', focusFunc)
    input.addEventListener('blur', blurFunc)
    if(input.value != "") {
        let parent = input.parentNode.parentNode;
        parent.classList.add('focus');
    }
});

function onChangeViewSpecies() {
    element = document.getElementsByClassName(this.id)[0];
    if(element.style.display == "none") {
        element.style.display = "block";
    } else {
        element.style.display = "none";
    }
}

species.forEach(input => {
    input.addEventListener('click', onChangeViewSpecies);
});

function clickFunc() {
    this.style.display = 'none';
}

flashNodes.forEach(flashNode => {
    flashNode.addEventListener('click', clickFunc)
});

function triggerPictureChoose() {
    document.querySelector('#image_loader').click();
}

function displayImage(e) {
    if (e.files[0]) {
        var reader = new FileReader();

        reader.onload = function(e) {
            document.querySelector('#profile_picture').setAttribute('src', e.target.result);
        }

        reader.readAsDataURL(e.files[0]);
    }
}

var slideIndex = 1;

showSlides(slideIndex);

// Next/previous controls
function plusSlides(n) {
  showSlides(slideIndex += n);
}

// Thumbnail image controls
function currentSlide(n) {
  showSlides(slideIndex = n);
}

function showSlides(n) {
  var i;
  var slides = document.getElementsByClassName("mySlides");
  var dots = document.getElementsByClassName("dot");
  if (n > slides.length) {
    slideIndex = 1;
  }
  if (n < 1) {
    slideIndex = slides.length;
  }
  for (i = 0; i < slides.length; i++) {
      slides[i].style.display = "none";
  }

  for (i = 0; i < dots.length; i++) {
      dots[i].className = dots[i].className.replace(" active", "");
  }

  slides[slideIndex - 1].style.display = "block";
  //dots[slideIndex - 1].className += " active";
}

function searchCharacters() {
    var input = document.getElementById("search");
    var filter = input.value.toUpperCase();
    var topics = document.getElementsByClassName('topic-section');
    var i;
    for(i = 0; i < topics.length; i++) {
        topic = topics[i];

        if(topic.className.toUpperCase().indexOf(filter) > -1) {
            topics[i].style.display = "";
        } else {
            topics[i].style.display = "none";
        }

    }

}



