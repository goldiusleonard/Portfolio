@extends('master.layout')

@section('title', 'Contact')
<link rel="stylesheet" href="{{ URL::asset('css/contact.css') }}">

@section('content')
<div class="promo">
    <h1 class="promoLabel">CONTACT</h1>
    <hr class="promoLine">
</div>

<div class="bookList">
    <div class="bookListSection">
        <div class="bookTitleSection">
            <h2 class="bookListTitle">OUR DETAIL</h2>
        </div>

        <div class="bookTable">
            <div class="storeLocationSection">
                <div class="titleSection">
                    <img src="{{ URL::asset('images/location.png') }}" alt="" class="storeLocationIcon">
                    <h2 class="storeLocationTitle">Store Location</h2>
                </div>

                <div class="contentSection">
                    <h3 class="address">
                        Jalan Pembangunan Baru Raya,<br>
                        Kompleks Pertokoan Emerald Blok III/12<br>
                        Bintaro, Tangerang Selatan<br>
                        Indonesia
                    </h3>
                </div>
            </div>

            <div class="openDailySection">
                <div class="titleSection">
                    <img src="{{ URL::asset('images/calendar.png') }}" alt="" class="storeLocationIcon">
                    <h2 class="openDailyTitle">Open Daily</h2>
                </div>

                <div class="contentSection">
                    <h3 class="address">
                        08.00 - 20.00
                    </h3>
                </div>
            </div>

            <div class="contactSection">
                <div class="titleSection">
                    <img src="{{ URL::asset('images/telephone.png') }}" alt="" class="storeLocationIcon">
                    <h2 class="contactTitle">Contact</h2>
                </div>

                <div class="contentSection">
                    <h3 class="address">
                        Phone   : 021-08899776655<br>
                        Email   : happybookstore@happy.com
                    </h3>
                </div>
            </div>
        </div>

    </div>

    <div class="categoryListSection">
        <div class="categoryTitleSection">
            <h2 class="categoryTitle">CATEGORY</h2>
        </div>

        <div class="categoryTable">
            <div class="scrollableCategory">
                @foreach ($categories as $category)
                    <a href="/category/{{ $category->id }}" class="tableContentCategory">
                        <h3 class="categoryText">{{ $category->category }}</h3>
                    </a>
                @endforeach
            </div>
        </div>

    </div>
</div>
@endsection
