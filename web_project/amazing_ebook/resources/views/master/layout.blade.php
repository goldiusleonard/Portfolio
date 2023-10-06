<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <link rel="shortcut icon" href="{{ URL::asset('images/logo.png') }}" type="image/x-icon">
    <title>@yield('title') | Amazing E-Book</title>
    <link rel="stylesheet" href="{{ URL::asset('css/layout.css') }}">
</head>
<body>
    <nav>
        <div class="logo-section">
            <a class="logo-btn" href="{{ route('home') }}">
                <img class="logo-icon" src="{{ URL::asset('images/logo.png') }}" alt="">
                <h3 class="logo-title">Amazing E-Book</h3>
            </a>
        </div>

        <div class="login-section">
            @guest
                <a class="sign-up-btn" href="{{ route('signup') }}">
                    <h3 class="sign-up-text">{{ __('Sign Up') }}</h3>
                </a>

                <a class="log-in-btn" href="{{ route('login') }}">
                    <h3 class="log-in-text">{{ __('Log In') }}</h3>
                </a>

                <div class="lang-dropdown">
                    <div class="lang-btn">
                        <h3 class="lang-text">{{ Config::get('languages')[App::getLocale()] }}</h3>
                        <img class="dropdown-arrow" src="{{ URL::asset('images/dropdown_arrow.png') }}" alt="">
                    </div>

                    <div class="lang-dropdown-content">
                        @foreach (Config::get('languages') as $lang => $language)
                            @if ($lang != App::getLocale())
                                <a class="dropdown-item" href="{{ route('lang.switch', $lang) }}"> {{$language}}</a>
                            @endif
                        @endforeach
                    </div>
                </div>
            @endguest

            @auth
                <a class="log-out-btn" href="{{ route('logout_process') }}">
                    <h3 class="log-out-text">{{ __('Log Out') }}</h3>
                </a>

                <div class="lang-dropdown">
                    <div class="lang-btn">
                        <h3 class="lang-text">{{ Config::get('languages')[App::getLocale()] }}</h3>
                        <img class="dropdown-arrow" src="{{ URL::asset('images/dropdown_arrow.png') }}" alt="">
                    </div>

                    <div class="lang-dropdown-content">
                        @foreach (Config::get('languages') as $lang => $language)
                            @if ($lang != App::getLocale())
                                <a class="dropdown-item" href="{{ route('lang.switch', $lang) }}"> {{$language}}</a>
                            @endif
                        @endforeach
                    </div>
                </div>

                <img class="photo-profile-img" src="{{ asset('storage/' . $user->display_picture_link) }}" alt="">
            @endauth
        </div>
    </nav>

    <div class="content-wrapper">
        @yield('content')
    </div>

    <footer>
        <p class="footer-copyright">&copy {{ __('Footer') }}</p>
    </footer>

</body>
</html>
