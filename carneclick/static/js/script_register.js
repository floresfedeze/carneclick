document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('registerForm');
    if (!form) return;

    const passwordInput = document.getElementById('password');
    const password2Input = document.getElementById('password2');

    function validatePassword() {
        const val = passwordInput.value;
        const hasMin8 = val.length >= 8;
        const hasUpper = /[A-Z]/.test(val);
        const hasDigit = /[0-9]/.test(val);

        if (!hasMin8 || !hasUpper || !hasDigit) {
            passwordInput.setCustomValidity(
                'La contraseña debe tener al menos 8 caracteres, incluido un número y una letra mayúscula.'
            );
        } else {
            passwordInput.setCustomValidity('');
        }
    }

    function validateConfirm() {
        if (password2Input.value !== passwordInput.value) {
            password2Input.setCustomValidity('Las contraseñas no coinciden.');
        } else {
            password2Input.setCustomValidity('');
        }
    }

    passwordInput.addEventListener('input', function () {
        validatePassword();
        validateConfirm();
    });

    password2Input.addEventListener('input', validateConfirm);
});
