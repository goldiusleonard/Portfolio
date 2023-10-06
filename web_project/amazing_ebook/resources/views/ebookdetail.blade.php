@extends('master.layout')

@section('title', $ebook->title)
<link rel="stylesheet" href="{{ URL::asset('css/ebookdetail.css') }}">

@section('content')
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

    <div class="container">
        <img class="ebook-detail-picture" src="{{ URL::asset('images/book_picture2.png') }}" alt="">
        <div class="ebook-detail">
            <h2 class="ebook-title">{{ $ebook->title }}</h2>
            <h3 class="ebook-author">{{  __('BY') }}: {{ $ebook->author }}</h3>
            <p class="ebook-description"><u>{{ __('Description') }}:</u><br><br>{{ $ebook->description }}</p>
        </div>
    </div>
    <form class="rent-form" method="post" action="/ebook_detail/{{ $ebook->id }}">
        @csrf
        <input class="rent-btn" type="submit" value="{{ __('Rent') }}">
    </form>
@endsection
