
var mix = {
    methods: {
        getSales() {
            this.getData("/api/products/limited")
                .then(data => {
                    this.salesCards = Array.isArray(data) ? data : [];
                })
                .catch(error => {
                    console.error("Не удалось загрузить товары:", error);
                    this.salesCards = [];
                });
        },
    },

    mounted() {
        this.getSales();
    },

    data() {
        return {
            salesCards: [],
        };
    },
};
