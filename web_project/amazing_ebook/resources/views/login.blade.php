@extends('master.layout')

@section('title', __('Log In'))
<link rel="stylesheet" href="{{ URL::asset('css/login.css') }}">

@section('content')
    <div class="banner-container">
        <div class="banner">
            <h1 class="banner-text">{{ __('LOG IN TO YOUR ACCOUNT') }}</h1>
        </div>
    </div>

    <div class="login-container">
        <form class="login-form" method="post" enctype="multipart/form-data" action="{{ route('login_process') }}">
            @csrf
            <div class="text-box">
                <label class="text-label" for="{{ __('Email_Address') }}">{{ __('Email Address') }}</label>
                <input class="text-input" type="email" name="{{ __('Email_Address') }}" id="{{ __('Email_Address') }}"
                    @error(__('Email_Address')) is-invalid @enderror>
            </div>

            @error(__('Email_Address'))
                <p class="errorAlert">{{$message}}</p>
            @enderror

            <div class="text-box">
                <label class="text-label" for="{{ __('Password_') }}">{{ __('Password') }}</label>
                <input class="text-input" type="password" name="{{ __('Password_') }}" id="{{ __('Password_') }}"
                    @error(__('Password_')) is-invalid @enderror>
            </div>

            @error(__('Password_'))
                <p class="errorAlert">{{$message}}</p>
            @enderror

            @if ($errors->any())
                <div class="text-box">
                    <label class="text-label" for=""> </label>
                    <div class="errorAlert">
                        @foreach ($errors->all() as $error)
                            @if ($error == __('Invalid Email or Password'))
                                <p>{{$error}}</p>
                            @elseif ($error == __('Your account is deactivated. Please contact the admin.'))
                                <p>{{$error}}</p>
                            @endif
                        @endforeach
                    </div>
                </div>
            @endif

            <div class="text-box">
                <label class="text-label" for=""> </label>
                <input type="checkbox" id="{{ __('Remember Me') }}" name="{{ __('Remember Me') }}" class="checkbox">
                <label for="remember">{{ __('Remember Me') }}</label>
            </div>

            <div class="text-box">
                <label class="text-label" for=""> </label>
                <input class="submit-btn" type="submit" value="{{ __('Log In') }}">
            </div>
        </form>
    </div>
@endsection
