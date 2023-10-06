<?php

namespace App\Http\Controllers;

use App\Models\categories;
use Illuminate\Http\Request;

class ContactController extends Controller
{
    public function displayView() {
        $categories = categories::all();

        return view('contact', compact('categories'));
    }
}
