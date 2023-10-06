@extends('master.layout')

@section('title', $currentCategory->category)
<link rel="stylesheet" href="{{ URL::asset('css/category.css') }}">

@section('content')
    <div class="promo {{$currentCategory->category}}">
        <h1 class="promoLabel">{{ Str::upper($currentCategory->category) }}</h1>
        <hr class="promoLine">
    </div>

    <div class="bookList">
        <div class="bookListSection">
            <div class="bookTitleSection">
                <h2 class="bookListTitle">BOOK LIST</h2>
            </div>

            <div class="bookTable">
                <div class="tableTitle">
                    <h3 class="titleColumn titleText">Title</h3>
                    <h3 class="authorColumn titleText">Author</h3>
                </div>

                @if ($books->isEmpty())
                    <div class="tableContentBooksEven">
                        <h3 class="titleColumn contentTextEven">No data ..</h3>
                    </div>
                @else
                    <div class="scrollableBook">
                        @php
                            $index = 0
                        @endphp
                        @foreach ($books as $book)
                            @if ($index % 2 == 0)
                                <a href="/detail/{{ $book->id }}" class="tableContentBooksEven">
                                    <h3 class="titleColumn contentTextEven">{{ $book->title }}</h3>
                                    <h3 class="authorColumn contentTextEven">{{ $book->details->author }}</h3>
                                </a>
                            @else
                                <a href="/detail/{{ $book->id }}" class="tableContentBooksOdd">
                                    <h3 class="titleColumn contentTextOdd">{{ $book->title }}</h3>
                                    <h3 class="authorColumn contentTextOdd">{{ $book->details->author }}</h3>
                                </a>
                            @endif
                            @php
                                $index += 1
                            @endphp
                        @endforeach
                    </div>
                @endif

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
