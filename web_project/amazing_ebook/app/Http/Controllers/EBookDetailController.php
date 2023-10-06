<?php

namespace App\Http\Controllers;

use App\Models\EBook;
use App\Models\Order;
use Illuminate\Http\Request;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\Auth;

class EbookDetailController extends Controller
{
    public function view($ebook_id) {
        $user = Auth::user();
        $ebook = EBook::where('id', $ebook_id)->get()->first();

        if ($ebook == null) {
            return redirect()->back();
        }

        return view('ebookdetail', compact('user', 'ebook'));
    }

    public function rent_process($ebook_id) {
        $user = Auth::user();
        $ebook = EBook::where('id', $ebook_id)->get()->first();

        $check = Order::where('user_id', $user->id)->where('ebook_id', $ebook->id)->first();

        if ($check == null)  {
            Order::create([
                'user_id' => $user->id,
                'ebook_id' => $ebook->id,
                'order_date' => Carbon::now()
            ]);
        }

        return redirect()->route('cart');
    }
}
