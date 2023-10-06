<?php

namespace App\Http\Controllers;

use App\Models\EBook;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class HomeController extends Controller
{
    public function view() {
        if (Auth::check()) {
            $user = Auth::user();
            $ebooks = EBook::paginate(10);

            return view('home', compact('user', 'ebooks'));
        }
        else {
            return view('home');
        }
    }
}
