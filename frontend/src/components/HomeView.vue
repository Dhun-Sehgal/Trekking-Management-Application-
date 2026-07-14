<template>
<div>

    <!-- Hero -->

    <section class="hero">

        <div class="container text-center text-white">

            <h1 class="display-3 fw-bold">
                Explore Nature with TrekPlatform
            </h1>

            <p class="lead mt-3">
                Discover breathtaking trekking destinations,
                book your adventure and create unforgettable memories.
            </p>

            <router-link
                to="/register"
                class="btn btn-success btn-lg me-3">

                Get Started

            </router-link>

            <router-link
                to="/login"
                class="btn btn-outline-light btn-lg">

                Login

            </router-link>

        </div>

    </section>

    <!-- About -->

    <section class="container py-5">

        <div class="row align-items-center">

            <div class="col-md-6">

                <h2 class="fw-bold">
                    About TrekPlatform
                </h2>

                <p class="text-muted">

                    TrekPlatform is an online trekking
                    management system where trekkers can
                    discover adventures, book treks,
                    manage bookings and explore nature
                    safely.

                </p>

                <p>

                    ✔ Easy Booking <br>
                    ✔ Verified Trek Staff <br>
                    ✔ Beautiful Destinations <br>
                    ✔ Trek History

                </p>

            </div>

            <div class="col-md-6 text-center">

                <img
                    src="/mountain.jpg"
                    class="img-fluid rounded shadow">

            </div>

        </div>

    </section>

    <!-- Features -->

    <section class="bg-light py-5">

        <div class="container">

            <h2 class="text-center mb-5">
                Why Choose Us?
            </h2>

            <div class="row text-center">

                <div class="col-md-4">

                    <h1>🏔</h1>

                    <h5>Beautiful Treks</h5>

                    <p>
                        Explore famous trekking
                        destinations across India.
                    </p>

                </div>

                <div class="col-md-4">

                    <h1>🎒</h1>

                    <h5>Easy Booking</h5>

                    <p>
                        Book your favourite trek
                        in just a few clicks.
                    </p>

                </div>

                <div class="col-md-4">

                    <h1>🌲</h1>

                    <h5>Safe Adventures</h5>

                    <p>
                        Guided by experienced
                        trek leaders.
                    </p>

                </div>

            </div>

        </div>

    </section>

</div>
</template>

<style scoped>

.hero{

    height:500px;

    background:url("/mountain.jpg");

    background-size:cover;

    background-position:center;

    display:flex;

    align-items:center;

    justify-content:center;

    position:relative;

}

.hero::before{

    content:"";

    position:absolute;

    inset:0;

    background:rgba(0,0,0,.45);

}

.hero .container{

    position:relative;

    z-index:2;

}

</style>