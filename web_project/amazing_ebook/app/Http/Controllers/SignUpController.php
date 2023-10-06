<?php

namespace App\Http\Controllers;

use App\Models\Gender;
use App\Models\Role;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules\Password;

class SignUpController extends Controller
{
    public function view() {
        $roles = Role::all();
        $genders = Gender::all();

        return view('signup', compact('roles', 'genders'));
    }

    public function signup_process(Request $request) {
        $newUser = $request->validate([
            __('First_Name') => 'required|alpha_num|max:25',
            __('Middle_Name') => 'nullable|alpha_num|max:25',
            __('Last_Name') => 'required|alpha_num|max:25',
            __('Gender_') => 'required',
            __('Email_Address') => 'required|email|unique:users,email',
            __('Role_') => 'required',
            __('Password_') => ['required', Password::min(8)->numbers()],
            __('Display_Picture') => 'required|image'
        ]);

        $savePath = 'storage/user_photos'; //path untuk function move()
        $imageName = $newUser[__('Email_Address')] . '.' . $newUser[__('Display_Picture')]->getClientOriginalExtension();

        $newUser[__('Display_Picture')]->move(public_path($savePath), $imageName);

        $tablePath = 'user_photos/' . $imageName; //path untuk dimasukkan kedalam table

        User::create([
            'first_name' => $newUser[__('First_Name')],
            'middle_name' => $newUser[__('Middle_Name')],
            'last_name' => $newUser[__('Last_Name')],
            'gender_id' => $newUser[__('Gender_')],
            'email' => $newUser[__('Email_Address')],
            'role_id' => $newUser[__('Role_')],
            'password' => Hash::make($newUser[__('Password_')]),
            'display_picture_link' => $tablePath,
            'delete_flag' => false
        ]);

        return redirect(route('login'));
    }
}
