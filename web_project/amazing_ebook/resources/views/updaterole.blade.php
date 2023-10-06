@extends('master.layout')

@section('title', __('Update Role'))
<link rel="stylesheet" href="{{ URL::asset('css/updaterole.css') }}">

@section('content')
    <div class="sub-menu">
        <div class="sub-menu-bar">
            <a class="menu-choice" href="{{ route('home') }}">{{ __('Home') }}</a>
            <a class="menu-choice" href="{{ route('cart') }}">{{ __('Cart') }}</a>
            <a class="menu-choice" href="{{ route('profile') }}">{{ __('Profile') }}</a>
            <a class="menu-choice selected" href="{{ route('account_maintenance') }}">{{ __('Account Maintenance') }}</a>
        </div>
    </div>

    <div class="container">
        <form class="update-form" method="post" action="/update_role/{{ $targetUser->id }}">
            @csrf
            <div class="form-row">
                <label class="update-label" for="">{{__('Name')}}:</label>
                @empty($targetUser->middle_name)
                    <p class="user-name">{{ $targetUser->first_name . " " . $targetUser->last_name }}</p>
                @else
                    <p class="user-name">{{ $targetUser->first_name . " " . $targetUser->middle_name . " " . $targetUser->last_name }}</p>
                @endempty
            </div>

            <div class="form-row">
                <label class="update-label" for="role">{{__('Role')}}:</label>
                <select class="role-select" name="role" id="role">
                    @foreach ($roles as $role)
                        @if ($role->id == $targetUser->role->id)
                            <option selected value="{{ $role->id }}">{{ $role->role_desc }}</option>
                        @else
                            <option value="{{ $role->id }}">{{ $role->role_desc }}</option>
                        @endif
                    @endforeach
                </select>
            </div>

            <input class="save-btn" type="submit" value="{{ __('Save') }}">
        </form>
    </div>
@endsection
