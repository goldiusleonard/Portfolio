<?php

namespace App\Http\Controllers;

use App\Models\books;
use App\Models\categories;
use Illuminate\Http\Request;

class CategoryController extends Controller
{
    public function displayView($category_id) {
        $categories = categories::all();
        $currentCategory = categories::all()->where('id', '=', $category_id)->first();
        $books = books::with('details')->where('categories_id', '=', $category_id)->get();

        return view('category', compact('categories', 'currentCategory', 'books'));
    }
}
