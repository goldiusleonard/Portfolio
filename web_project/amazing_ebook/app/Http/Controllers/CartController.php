<?php

namespace App\Http\Controllers;

use App\Models\Order;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class CartController extends Controller
{
    public function view() {
        $user = Auth::user();
        $orders = Order::where('user_id', $user->id)->paginate(10);

        return view('cart', compact('user', 'orders'));
    }

    public function checkout_process() {
        $user = Auth::user();
        $orders = Order::where('user_id', $user->id)->get();

        foreach ($orders as $order) {
            $order->delete();
        }

        return view('checkout', compact('user'));
    }

    public function delete_order_process($order_id) {
        $order = Order::where('id', $order_id)->get()->first();

        $order->delete();

        return redirect()->back();
    }
}
