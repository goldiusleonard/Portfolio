<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;

class LogInController extends Controller
{
    public function view() {
        return view('login');
    }

    public function login_process(Request $request) {
        $user = $request->validate([
            __('Email_Address') => 'required|email',
            __('Password_') => 'required'
        ]);

        $rememberMe = $request->hasAny(__('Remember_Me'));

        $userData = User::where('email', $user[__('Email_Address')])->get()->first();

        if ($userData != null && $userData->delete_flag == false) {
            if (Auth::attempt(["email" => $user[__('Email_Address')], "password" => $user[__('Password_')]], $rememberMe)) {
                return redirect()->route('home');
            }
        }
        else if ($userData != null && $userData->delete_flag == true) {
            return redirect()->back()->withErrors(__('Your account is deactivated. Please contact the admin.'));
        }

        return redirect()->back()->withErrors(__('Invalid Email or Password'));
    }
}
