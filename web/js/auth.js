// ===============================
// USUARIOS DEL SISTEMA
// ===============================

const usuarios = [
    { usuario: "admin", password: "admin123", rol: "ADMIN" },
    { usuario: "consulta", password: "consulta123", rol: "CONSULTA" }
];

// ===============================
// LOGIN
// ===============================

function login() {

    const userInput = document.getElementById("usuario").value;
    const passInput = document.getElementById("password").value;

    const usuarioValido = usuarios.find(u =>
        u.usuario === userInput && u.password === passInput
    );

    if (!usuarioValido) {
        document.getElementById("error").innerText = "Usuario o contraseña incorrectos";
        return;
    }

    localStorage.setItem("usuario", JSON.stringify(usuarioValido));

    if (usuarioValido.rol === "ADMIN") {
        window.location.href = "admin.html";
    } else {
        window.location.href = "dashboard.html";
    }
}

// ===============================
// VERIFICAR SESIÓN
// ===============================

function verificarSesion(rolRequerido = null) {

    const usuario = JSON.parse(localStorage.getItem("usuario"));

    if (!usuario) {
        window.location.href = "login.html";
        return;
    }

    if (rolRequerido && usuario.rol !== rolRequerido) {
        alert("No tienes permisos para acceder a esta sección");
        window.location.href = "dashboard.html";
    }
}

// ===============================
// LOGOUT
// ===============================

function logout() {
    localStorage.removeItem("usuario");
    window.location.href = "login.html";
}

function volverInicio() {
    window.location.href = "index.html";
}

function togglePassword() {
    const input = document.getElementById("password");
    input.type = input.type === "password" ? "text" : "password";
}

// Login con Enter
document.addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        login();
    }
});