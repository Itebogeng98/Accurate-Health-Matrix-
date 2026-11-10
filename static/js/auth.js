(() => {
    document.querySelectorAll('.password-toggle').forEach(button => {
        const input = document.getElementById(button.getAttribute('aria-controls'));
        button.hidden = false;
        button.addEventListener('click', () => {
            const visible = input.type === 'password';
            input.type = visible ? 'text' : 'password';
            button.setAttribute('aria-pressed', String(visible));
            const label = input.name === 'confirm_password' ? 'confirm password' : 'password';
            button.setAttribute('aria-label', `${visible ? 'Hide' : 'Show'} ${label}`);
        });
    });
    const input = document.querySelector('[data-password-strength]');
    if (!input) return;
    const confirmation = document.getElementById('id_confirm_password');
    if (confirmation) {
        const matchFeedback = document.getElementById('confirm-password-feedback');
        const checkMatch = () => {
            const mismatch = confirmation.value !== '' && confirmation.value !== input.value;
            confirmation.setCustomValidity(mismatch ? 'Passwords do not match.' : '');
            confirmation.setAttribute('aria-invalid', String(mismatch));
            matchFeedback.textContent = confirmation.value ? (mismatch ? 'Passwords do not match.' : 'Passwords match.') : '';
        };
        confirmation.addEventListener('input', checkMatch);
        input.addEventListener('input', checkMatch);
        input.form.addEventListener('submit', checkMatch);
        checkMatch();
    }
    const meter = document.querySelector('.password-meter');
    const feedback = document.getElementById('password-feedback');
    meter.hidden = false;
    const update = () => {
        const value = input.value;
        let score = 0;
        if (value.length >= 12) score++;
        if (value.length >= 16) score++;
        if (/[a-z]/.test(value) && /[A-Z]/.test(value)) score++;
        if (/[^a-zA-Z]/.test(value)) score++;
        if (value.length < 6) score = Math.min(score, 1);
        if (/^(.)\1+$/.test(value) || /^\d+$/.test(value)) score = Math.min(score, 1);
        meter.value = score;
        feedback.textContent = !value ? '' : value.length < 6
            ? `Add ${6 - value.length} more characters to reach the minimum.`
            : ['Weak — add more variety.', 'Weak — use less predictable words.', 'Fair — add length or variety.', 'Good — a longer passphrase is even better.', 'Strong length and variety.'][score];
    };
    input.addEventListener('input', update);
    update();
})();
