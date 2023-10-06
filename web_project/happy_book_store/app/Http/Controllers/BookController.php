<?php

namespace App\Http\Controllers;

use App\Models\books;
use App\Models\categories;
use Illuminate\Http\Request;

class BookController extends Controller
{
    public function displayView($book_id) {
        $categories = categories::all();
        $book = books::with('details')->with('categories')->where('id', '=', $book_id)->first();

        return view('detail', compact('categories', 'book'));
    }
}
