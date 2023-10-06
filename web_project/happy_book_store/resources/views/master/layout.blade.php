<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>@yield("title") | Happy Book Store</title>
    <link rel="shortcut icon" href="{{ URL::asset('images/logo.png') }}" type="image/x-icon">
    <link rel="stylesheet" href="{{ URL::asset('css/layout.css') }}">
</head>
<body>
    <nav>
        <div class="logoSection">
            <a href="/" class="logo"><img src="{{ URL::asset('images/logo.png')}}" alt="" class="logo"></a>
            <h2 class="title">Happy Book Store</h2>
        </div>

        <div class="menuSection">
            <a href="/" class="menuBtn">
                <h2>Home</h2>
            </a>
            <div class="dropDown">
                <div class="dropDownBtn">
                    <h2>Category</h2>
                    <img src="{{ URL::asset('images/dropDownArrow.png')}}" alt="" class="dropDownArrow">
                </div>
                <div class="dropDownContent">
                    @foreach ($categories as $category)
                        <a href="/category/{{$category->id}}" class="dropDownItem">
                            {{$category->category}}
                        </a>
                    @endforeach
                </div>
            </div>
            <a href="/contact" class="menuBtn">
                <h2>Contact</h2>
            </a>
        </div>
    </nav>

    <div class="content">
        @yield("content")
    </div>

    <footer>
        <h3 class="copyright">© 2021 Copyright Happy Book Store</h3>
    </footer>

</body>
</html>
