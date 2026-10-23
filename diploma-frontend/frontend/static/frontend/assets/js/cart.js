
var mix = {
    methods: {
        submitBasket() {
            // Не создаём заказ, если пользователь не авторизован.
            const isAuthenticated =
                document.body.dataset.authenticated === 'true';

            if (!isAuthenticated) {
                // После входа нужно вернуться к корзине.
                location.assign('/sign-in/?next=/cart/');
                return;
            }

            // Заказ создаётся только для авторизованного пользователя.
            this.postData('/api/orders', Object.values(this.basket))
                .then(({ data: { orderId } }) => {
                    location.assign(`/orders/${orderId}/`);
                })
                .catch(() => {
                    console.warn('Ошибка при создании заказа');
                    alert('Не удалось создать заказ. Попробуйте ещё раз.');
                });
        }
    },

    mounted() {},

    data() {
        return {};
    }
};
