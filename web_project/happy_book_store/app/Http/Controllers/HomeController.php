<?php

namespace App\Http\Controllers;

use App\Models\books;
use App\Models\categories;
use Illuminate\Http\Request;

class HomeController extends Controller
{
    public function displayView() {
        $categories = categories::all();
        $books = books::with('details')->get();

        return view('home', compact('categories', 'books'));
    }
}
