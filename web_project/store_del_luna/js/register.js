// window.onload = function(){
    function validateRegister(){
        document.getElementById('username-error').innerText=''
        document.getElementById('pass-error').innerText=''
        document.getElementById('confpass-error').innerText=''
        document.getElementById('name-error').innerText=''
        document.getElementById('gender-error').innerText=''
        document.getElementById('email-error').innerText=''
        document.getElementById('age-error').innerText=''
        document.getElementById('agree-error').innerText=''
    
        let username = document.forms.registrationForm.username.value
        let pass = document.forms.registrationForm.password.value
        let confpass = document.forms.registrationForm.confpassword.value
        let name = document.forms.registrationForm.name.value
        let gender = document.forms.registrationForm.gender.value
        let email = document.forms.registrationForm.email.value
        let age = document.forms.registrationForm.age.value
        let checkbox = document.forms.registrationForm.agree.checked
        
        let count = 0
        
        if(username == ''){
            document.getElementById('username-error').innerText='Username cannot be empty!'
            // alert("Username cannot be empty!")
        }
        else{
            if(username.length < 8){
                document.getElementById('username-error').innerText='Username must be more than 7 characters!'
                // alert("Username must be more than 7 characters!")
            }else count++
        }
    
        if(pass == ''){
            document.getElementById('pass-error').innerText='Password cannot be empty!'
            // alert("Password cannot be empty!")
        }
        else{
            if(pass.length < 6){
                document.getElementById('pass-error').innerText='Password must be more than 5 characters!'
                // alert("'Password must be more than 5 characters!'")
            }else count++
        }
    
        if(confpass == ''){
            document.getElementById('confpass-error').innerText='Confirmation cannot be empty!'
            // alert("Confirmation cannot be empty!")
        }
        else{
            if(confpass != pass){
                document.getElementById('confpass-error').innerText='Confirmation password must be same with password!'
                // alert("Confirmation password must be same with password!")
            }else count++
        }
    
        if(name == ''){
            document.getElementById('name-error').innerText='Full name cannot be empty!'
            // alert("Full name cannot be empty!")
        }
        else{
            if(name.length < 3){
                document.getElementById('name-error').innerText='Full name must be more than 2 alphabet!'
                // alert("Full name must be more than 2 alphabet!")
            }else count++
        }
    
        if(gender == ''){
            document.getElementById('gender-error').innerText='Gender must be chosen!'
            // alert("Gender must be chosen!")
        }else count++
    
        if(email == ''){
            document.getElementById('email-error').innerText='Email cannot be empty!'
            // alert("Email cannot be empty!")
        }
        else{
            if(!email.endsWith('.com')){
                document.getElementById('email-error').innerText='Email must be ends with \'.com\'!'
                // alert("Email must be ends with \'.com\'!")
            }else count++
        }
    
        if(age == ''){
            document.getElementById('age-error').innerText='Age cannot be empty!'
            // alert("Age cannot be empty!")
        }
        else{
            if(age <= 0 || age >= 120 ){
                document.getElementById('age-error').innerText='Age cannot be minus number or zero and age cannot be more than or equal 120!'
                // alert("Age cannot be minus number or zero and age cannot be more than or equal 120!")
            }else count++
        }
    
        if(checkbox==false){
            document.getElementById('agree-error').innerText='The term and contiditon statement must be checked!'
            // alert("The term and contiditon statement must be checked!")
        }else count++
    
        if(count==8){
            alert("Register success!")
            // location.href = 'home.html';
            location.assign('home.html')
        }
        else if(count<8){
            alert("Your input data is not correctly!")
        }
        
        return false
    } 
// }