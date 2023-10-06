@extends('master.layout')

@section('title', __('Log Out'))
<link rel="stylesheet" href="{{ URL::asset('css/logout.css') }}">

@section('content')
    <div class="container">
        <img class="logout-icon" src="{{ URL::asset('images/check_icon.png') }}" alt="">
        <h2 class="logout-text">{{ __('Log Out Success') }}</h2>
    </div>
@endsection
