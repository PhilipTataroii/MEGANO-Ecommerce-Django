
var mix = {
    methods: {
        signIn() {
            const username = document.querySelector('#login').value;
            const password = document.querySelector('#password').value;

            this.postData(
                '/api/sign-in',
                JSON.stringify({ username, password })
            )
                .then(({ data, status }) => {
                    // Получаем адрес возврата после авторизации.
                    const params = new URLSearchParams(
                        window.location.search
                    );

                    const next = params.get('next');

                    // Разрешаем переходы только внутри нашего сайта.
                    if (
                        next &&
                        next.startsWith('/') &&
                        !next.startsWith('//') &&
                        !next.includes('\\')
                    ) {
                        location.assign(next);
                    } else {
                        location.assign('/');
                    }
                })
                .catch(() => {
                    alert('Ошибка авторизации!');
                });
        }
    },

    mounted() {},

    data() {
        return {};
    }
};
