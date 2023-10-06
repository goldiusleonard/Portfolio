<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class AccountMaintenanceController extends Controller
{
    public function view() {
        $user = Auth::user();
        $accounts = User::where('id', '!=', $user->id)->paginate(10);

        return view('accountmaintenance', compact('user', 'accounts'));
    }

    public function delete_user_process($user_id) {
        $targetUser = User::where('id', $user_id)->first();

        $targetUser->delete_flag = true;
        $targetUser->save();

        return redirect()->back();
    }

public function recover_user_process($user_id) {
        $targetUser = User::where('id', $user_id)->first();

        $targetUser->delete_flag = false;
        $targetUser->save();

        return redirect()->back();
    }
}
