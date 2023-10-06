@extends('master.layout')

@section('title', __('Home'))
<link rel="stylesheet" href="{{ URL::asset('css/home.css') }}">

@section('content')
    <div class="banner-container">
        <div class="banner">
            <h1 class="banner-text">{{ __('Find & Rent Your E-Book Here!') }}</h1>
        </div>
    </div>
    @guest
        <div class="get-started-section">
            <img class="get-started-icon" src="{{ URL::asset('images/book_picture.png') }}" alt="">

            <div class="right-get-started">
                <h4 class=""></h4>
                <h2 class="right-get-started-text">{{ __('no account') }}</h2>
                <a class="get-started-btn" href="{{ route('signup') }}">
                    {{ __('Get Started') }}
                </a>
            </div>
        </div>
    @endguest

    @auth
        <div class="sub-menu">
            <div class="sub-menu-bar">
                @if ($user->role->role_desc == 'User')
                    <a class="menu-choice selected" href="{{ route('home') }}">{{ __('Home') }}</a>
                    <a class="menu-choice" href="{{ route('cart') }}">{{ __('Cart') }}</a>
                    <a class="menu-choice" href="{{ route('profile') }}">{{ __('Profile') }}</a>
                @elseif ($user->role->role_desc == 'Admin')
                    <a class="menu-choice selected" href="{{ route('home') }}">{{ __('Home') }}</a>
                    <a class="menu-choice" href="{{ route('cart') }}">{{ __('Cart') }}</a>
                    <a class="menu-choice" href="{{ route('profile') }}">{{ __('Profile') }}</a>
                    <a class="menu-choice" href="{{ route('account_maintenance') }}">{{ __('Account Maintenance') }}</a>
                @endif
            </div>
        </div>

        <div class="ebook-section">
            <h2 class="ebook-section-title">{{ __('E-Book Collections')}}</h2>

            @if ($ebooks->isEmpty())
                <div class="ebook-list">
                    <img class="ebook-list-empty-icon" src="{{ URL::asset('images/empty_icon.png') }}" alt="">
                    <h3 class="ebook-list-empty">{{ __('ebook list empty') }}</h3>
                </div>
            @else
                <div class="ebook-list">
                    @foreach ($ebooks as $ebook)
                        <a class="ebook-item" href="/ebook_detail/{{ $ebook->id }}">
                            <h3 class="ebook-title">{{ $ebook->title }}</h3>
                            <h5 class="ebook-author">{{ __('Author') }}: {{ $ebook->author }}</h5>
                        </a>
                    @endforeach
                </div>
            @endif

            @if ($ebooks->lastPage() > 1)
                <div class="pagination">
                    @if ($ebooks->currentPage() > 1)
                        <a class="pagination-btn" href="{{ $ebooks->url($ebooks->currentPage() - 1) }}">{{ __('Previous') }}</a>
                    @endif

                    <p class="pagination-page">{{ $ebooks->firstItem() }} - {{ $ebooks->lastItem() }} {{ __('of') }} {{ $ebooks->total() }}</p>

                    @if ($ebooks->currentPage() != $ebooks->lastPage())
                        <a class="pagination-btn" href="{{ $ebooks->url($ebooks->currentPage() + 1) }}">{{ __('Next') }}</a>
                    @endif
                </div>
            @endif
        </div>
    @endauth
@endsection
