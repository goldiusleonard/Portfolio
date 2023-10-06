@extends('master.layout')

@section('title', $book->title)
<link rel="stylesheet" href="{{ URL::asset('css/detail.css') }}">

@section('content')
    <div class="promo {{ $book->categories->category }}">
        <h1 class="promoLabel">{{ Str::upper($book->title) }}</h1>
        <hr class="promoLine">
    </div>

    <div class="bookList">
        <div class="bookListSection">
            <div class="bookTitleSection">
                <h2 class="bookListTitle">BOOK DETAIL</h2>
            </div>

            <div class="bookTable">
                <h2 class="detail titleDetail">{{ $book->title }}</h2>
                <h2 class="detail yearDetail">{{ $book->details->year }}</h2>
                <br>
                <h2 class="detail authorDetail">By : {{ $book->details->author }} (author)</h2>
                <h2 class="detail publisherDetail">Published by : {{ $book->details->publisher }}</h2>
                <br>
                <br>
                <h2 class="detail descriptionDetail">Description:</h2>
                <h2 class="description">{{ $book->details->description }}</h2>
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
