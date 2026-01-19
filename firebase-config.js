// Firebase Configuration for La Lupa
// IMPORTANT: Replace these values with your Firebase project credentials
// Get them from: Firebase Console > Project Settings > Your apps > Web app

const firebaseConfig = {
    apiKey: "AIzaSyDdJOinP5e_R-X1lNOnSMnL7DpI9FyUmhE",
    authDomain: "lalupa0101.firebaseapp.com",
    projectId: "lalupa0101",
    storageBucket: "lalupa0101.firebasestorage.app",
    messagingSenderId: "787575110662",
    appId: "1:787575110662:web:8a0228b28500c764565787",
    measurementId: "G-68S1GCTY4J"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize services
const auth = firebase.auth();
const db = firebase.firestore();

// Admin email - this user will have admin privileges
const ADMIN_EMAIL = "admin@ciudadbilingue.com";

// Auth state management
let currentUser = null;
let isAdmin = false;
let userIsBlocked = false;

// Auth state observer
auth.onAuthStateChanged(async (user) => {
    currentUser = user;

    if (user) {
        // Check if user is admin
        isAdmin = user.email === ADMIN_EMAIL;

        // Check if user is blocked
        userIsBlocked = await checkIfUserBlocked(user.uid);

        // Create or update user profile in Firestore
        await createOrUpdateUserProfile(user);

        // Update UI
        updateAuthUI(true);

        console.log('Usuario autenticado:', user.email, isAdmin ? '(Admin)' : '');
    } else {
        isAdmin = false;
        userIsBlocked = false;
        updateAuthUI(false);
        console.log('Usuario no autenticado');
    }
});

// Create or update user profile
async function createOrUpdateUserProfile(user) {
    try {
        const userRef = db.collection('users').doc(user.uid);
        const userDoc = await userRef.get();

        if (!userDoc.exists) {
            // Create new user profile
            await userRef.set({
                email: user.email,
                displayName: user.displayName || user.email.split('@')[0],
                photoURL: user.photoURL || null,
                isBlocked: false,
                createdAt: firebase.firestore.FieldValue.serverTimestamp(),
                lastLogin: firebase.firestore.FieldValue.serverTimestamp()
            });
        } else {
            // Update last login
            await userRef.update({
                lastLogin: firebase.firestore.FieldValue.serverTimestamp()
            });
        }
    } catch (error) {
        console.error('Error creating/updating user profile:', error);
    }
}

// Check if user is blocked
async function checkIfUserBlocked(userId) {
    try {
        const userDoc = await db.collection('users').doc(userId).get();
        if (userDoc.exists) {
            return userDoc.data().isBlocked === true;
        }
        return false;
    } catch (error) {
        console.error('Error checking blocked status:', error);
        return false;
    }
}

// Sign in with email/password
async function signInWithEmail(email, password) {
    try {
        const result = await auth.signInWithEmailAndPassword(email, password);
        closeAuthModal();
        showNotification('Bienvenido de vuelta!', 'success');
        return result.user;
    } catch (error) {
        handleAuthError(error);
        throw error;
    }
}

// Sign up with email/password
async function signUpWithEmail(email, password, displayName) {
    try {
        const result = await auth.createUserWithEmailAndPassword(email, password);

        // Update display name
        await result.user.updateProfile({
            displayName: displayName
        });

        closeAuthModal();
        showNotification('Cuenta creada exitosamente!', 'success');
        return result.user;
    } catch (error) {
        handleAuthError(error);
        throw error;
    }
}

// Sign in with Google
async function signInWithGoogle() {
    try {
        const provider = new firebase.auth.GoogleAuthProvider();
        provider.setCustomParameters({
            prompt: 'select_account'
        });

        const result = await auth.signInWithPopup(provider);
        closeAuthModal();
        showNotification('Bienvenido ' + (result.user.displayName || 'Usuario') + '!', 'success');
        return result.user;
    } catch (error) {
        handleAuthError(error);
        throw error;
    }
}

// Sign out
async function signOut() {
    try {
        await auth.signOut();
        showNotification('Sesion cerrada', 'info');
    } catch (error) {
        console.error('Error signing out:', error);
        showNotification('Error al cerrar sesion', 'error');
    }
}

// Handle authentication errors
function handleAuthError(error) {
    let message = 'Error de autenticacion';

    switch (error.code) {
        case 'auth/email-already-in-use':
            message = 'Este correo ya esta registrado';
            break;
        case 'auth/invalid-email':
            message = 'Correo electronico invalido';
            break;
        case 'auth/operation-not-allowed':
            message = 'Operacion no permitida';
            break;
        case 'auth/weak-password':
            message = 'La contrasena debe tener al menos 6 caracteres';
            break;
        case 'auth/user-disabled':
            message = 'Esta cuenta ha sido deshabilitada';
            break;
        case 'auth/user-not-found':
            message = 'No existe una cuenta con este correo';
            break;
        case 'auth/wrong-password':
            message = 'Contrasena incorrecta';
            break;
        case 'auth/popup-closed-by-user':
            message = 'Inicio de sesion cancelado';
            break;
        case 'auth/network-request-failed':
            message = 'Error de conexion. Verifica tu internet';
            break;
        default:
            message = error.message;
    }

    showNotification(message, 'error');
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
        <span>${message}</span>
    `;

    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);

    // Remove after delay
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Update Auth UI based on auth state
function updateAuthUI(isLoggedIn) {
    const authButton = document.getElementById('auth-button');
    const authButtonHero = document.getElementById('auth-button-hero');
    const adminPanel = document.getElementById('admin-panel-btn');
    const editModeBtn = document.getElementById('edit-mode-btn');

    if (authButton) {
        if (isLoggedIn && currentUser) {
            const displayName = currentUser.displayName || currentUser.email.split('@')[0];
            authButton.innerHTML = `
                <i class="fas fa-user-circle"></i>
                <span>${displayName}</span>
                <i class="fas fa-chevron-down"></i>
            `;
            authButton.classList.add('logged-in');
            authButton.onclick = toggleUserMenu;
        } else {
            authButton.innerHTML = `
                <i class="fas fa-sign-in-alt"></i>
                <span>Iniciar Sesion</span>
            `;
            authButton.classList.remove('logged-in');
            authButton.onclick = openAuthModal;
        }
    }

    // Hero auth button (same behavior)
    if (authButtonHero) {
        if (isLoggedIn && currentUser) {
            authButtonHero.style.display = 'none';
        } else {
            authButtonHero.style.display = 'inline-flex';
            authButtonHero.onclick = openAuthModal;
        }
    }

    // Admin-only elements
    if (adminPanel) {
        adminPanel.style.display = isAdmin ? 'inline-flex' : 'none';
    }

    if (editModeBtn) {
        editModeBtn.style.display = isAdmin ? 'inline-flex' : 'none';
    }

    // Update comment sections if modal is open
    if (document.getElementById('caso-modal')?.classList.contains('active')) {
        updateCommentSection();
    }
}

// Toggle user menu dropdown
function toggleUserMenu(e) {
    e.stopPropagation();

    let menu = document.getElementById('user-menu');

    if (menu) {
        menu.remove();
        return;
    }

    const button = e.currentTarget;
    const rect = button.getBoundingClientRect();

    menu = document.createElement('div');
    menu.id = 'user-menu';
    menu.className = 'user-menu';
    menu.innerHTML = `
        <div class="user-menu-header">
            <strong>${currentUser.displayName || currentUser.email.split('@')[0]}</strong>
            <small>${currentUser.email}</small>
        </div>
        <div class="user-menu-divider"></div>
        ${isAdmin ? '<a href="#" class="user-menu-item" onclick="openAdminPanel(); return false;"><i class="fas fa-user-shield"></i> Panel de Admin</a>' : ''}
        <a href="#" class="user-menu-item" onclick="signOut(); return false;"><i class="fas fa-sign-out-alt"></i> Cerrar Sesion</a>
    `;

    menu.style.top = (rect.bottom + 8) + 'px';
    menu.style.right = (window.innerWidth - rect.right) + 'px';

    document.body.appendChild(menu);

    // Close on click outside
    setTimeout(() => {
        document.addEventListener('click', closeUserMenu);
    }, 10);
}

function closeUserMenu() {
    const menu = document.getElementById('user-menu');
    if (menu) menu.remove();
    document.removeEventListener('click', closeUserMenu);
}

// Auth Modal Functions
function openAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        // Focus first input
        setTimeout(() => {
            const firstInput = modal.querySelector('input');
            if (firstInput) firstInput.focus();
        }, 100);
    }
}

function closeAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
        // Clear form
        const form = modal.querySelector('form');
        if (form) form.reset();
    }
}

// Switch between login and register modes
function switchAuthMode(mode) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');

    if (mode === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        loginTab.classList.remove('active');
        registerTab.classList.add('active');
    }
}

// Password reset
async function sendPasswordReset(email) {
    try {
        await auth.sendPasswordResetEmail(email);
        showNotification('Correo de recuperacion enviado', 'success');
    } catch (error) {
        handleAuthError(error);
    }
}
