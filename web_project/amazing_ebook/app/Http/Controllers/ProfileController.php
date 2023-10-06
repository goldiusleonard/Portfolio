<?php

namespace App\Http\Controllers;

use App\Models\Gender;
use App\Models\Role;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules\Password;

class ProfileController extends Controller
{
    public function view() {
        $user = Auth::user();
        $genders = Gender::all();
        $roles = Role::all();

        return view('profile', compact('user', 'genders', 'roles'));
    }

    public function update_profile(Request $request) {
        $user = Auth::user();

        $newInfo = $request->validate([
            __('First_Name') => 'required|alpha_num|max:25',
            __('Middle_Name') => 'nullable|alpha_num|max:25',
            __('Last_Name') => 'required|alpha_num|max:25',
            __('Gender_') => 'required',
            __('Email_Address') => 'required|email|unique:users,email,'.$user->id,
            __('Role_') => 'required',
            __('Password_') => ['required', Password::min(8)->numbers()],
            __('Display_Picture') => 'required|image'
        ]);

        $currentUser = User::where('id', $user->id)->first();

        $current_path = public_path('storage/' . $currentUser->display_picture_link);

        File::delete($current_path);

        $savePath = 'storage/user_photos'; //path untuk function move()
        $imageName = $request[__('Email_Address')] . '.' . $request[__('Display_Picture')]->getClientOriginalExtension();

        $request[__('Display_Picture')]->move(public_path($savePath), $imageName);

        $tablePath = 'user_photos/' . $imageName; //path untuk dimasukkan kedalam table

        $currentUser->first_name = $newInfo[__('First_Name')];
        $currentUser->middle_name = $newInfo[__('Middle_Name')];
        $currentUser->last_name = $newInfo[__('Last_Name')];
        $currentUser->gender_id = $newInfo[__('Gender_')];
        $currentUser->email = $newInfo[__('Email_Address')];
        $currentUser->role_id = $newInfo[__('Role_')];
        $currentUser->password = Hash::make($newInfo[__('Password_')]);
        $currentUser->display_picture_link = $tablePath;

        $currentUser->save();

        $user = Auth::user();

        return view('saveprofile', compact('user'));
    }
}
