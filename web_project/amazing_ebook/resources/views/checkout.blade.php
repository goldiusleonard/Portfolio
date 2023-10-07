@extends('master.layout')

@section('title', __('Checkout Success'))
<link rel="stylesheet" href="{{ URL::asset('css/checkout.css') }}">

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
        <img class="checkout-icon" src="{{ URL::asset('images/check_icon.png') }}" alt="">
        <h2 class="checkout-text">{{  __('Checkout Success') }}</h2>
    </div>
@endsection