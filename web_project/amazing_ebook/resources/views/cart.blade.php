@extends('master.layout')

@section('title', __('Cart'))
<link rel="stylesheet" href="{{ URL::asset('css/cart.css') }}">

@section('content')
    <div class="sub-menu">
        <div class="sub-menu-bar">
            @if ($user->role->role_desc == 'User')
                <a class="menu-choice" href="{{ route('home') }}">{{ __('Home') }}</a>
                <a class="menu-choice selected" href="{{ route('cart') }}">{{ __('Cart') }}</a>
                <a class="menu-choice" href="{{ route('profile') }}">{{ __('Profile') }}</a>
            @elseif ($user->role->role_desc == 'Admin')
                <a class="menu-choice" href="{{ route('home') }}">{{ __('Home') }}</a>
                <a class="menu-choice selected" href="{{ route('cart') }}">{{ __('Cart') }}</a>
                <a class="menu-choice" href="{{ route('profile') }}">{{ __('Profile') }}</a>
                <a class="menu-choice" href="{{ route('account_maintenance') }}">{{ __('Account Maintenance') }}</a>
            @endif
        </div>
    </div>

    <div class="container">
        <div class="order-section">
            <h2 class="order-section-title">{{ __('My Cart') }}</h2>

            @if ($orders->isEmpty())
                <div class="order-list">
                    <img class="order-list-empty-icon" src="{{ URL::asset('images/empty_icon.png') }}" alt="">
                    <h3 class="order-list-empty">{{ __('order list empty') }}</h3>
                </div>
            @else
                <div class="order-list">
                    @foreach ($orders as $order)
                        <a class="order-item" href="/ebook_detail/{{ $order->ebook->id }}">
                            <form method="post" action="/delete_order/{{ $order->id }}" class="order-form">
                                @csrf
                                <div class="order-detail">
                                    <h3 class="order-title">{{ $order->ebook->title }}</h3>
                                    <h5 class="order-author">{{  __('Author') }}: {{ $order->ebook->author }}</h5>
                                </div>
                                <button class="delete-btn" type="submit" value="Delete">
                                    <img class="delete-img" src="{{ URL::asset('images/delete_btn.png') }}" alt="">
                                </button>
                            </form>
                        </a>
                    @endforeach
                </div>
            @endif

            @if ($orders->lastPage() > 1)
                <div class="pagination">
                    @if ($orders->currentPage() > 1)
                        <a class="pagination-btn" href="{{ $orders->url($orders->currentPage() - 1) }}">{{ __('Previous') }}</a>
                    @endif

                    <p class="pagination-page">{{ $orders->firstItem() }} - {{ $orders->lastItem() }} {{ __('of') }} {{ $orders->total() }}</p>

                    @if ($orders->currentPage() != $orders->lastPage())
                        <a class="pagination-btn" href="{{ $orders->url($orders->currentPage() + 1) }}">{{ __('Next') }}</a>
                    @endif
                </div>
            @endif
        </div>
    </div>
    @if ($orders->total() > 0)
        <form class="checkout-form" method="post" action="/cart">
            @csrf
            <input class="checkout-btn" type="submit" value="{{ __('Checkout') }}">
        </form>
    @endif
@endsection
