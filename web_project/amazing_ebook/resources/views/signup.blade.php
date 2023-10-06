@extends('master.layout')

@section('title', __('Sign Up'))
<link rel="stylesheet" href="{{ URL::asset('css/signup.css') }}">

@section('content')
    <div class="banner-container">
        <div class="banner">
            <h1 class="banner-text">{{__('SIGN UP YOUR ACCOUNT')}}</h1>
        </div>
    </div>

    <div class="signup-container">
        <form method="post" action="{{ route('signup_process') }}" enctype="multipart/form-data" class="signup-form">
            @csrf
            <div class="signup-content">
                <div class="left-signup-content">
                    <div class="text-box">
                        <label class="text-label" for="{{__('First_Name')}}">{{__('First Name')}}</label>
                        <input class="text-input" type="text" name="{{__('First_Name')}}" id="{{__('First_Name')}}"
                            @error(__('First_Name')) is-invalid @enderror>
                    </div>

                    @error(__('First_Name'))
                        <p class="errorAlert">{{$message}}</p>
                    @enderror

                    <div class="text-box">
                        <label class="text-label" for="{{__('Last_Name')}}">{{__('Last Name')}}</label>
                        <input class="text-input" type="text" name="{{__('Last_Name')}}" id="{{__('Last_Name')}}"
                            @error(__('Last_Name')) is-invalid @enderror>
                    </div>

                    @error(__('Last_Name'))
                        <p class="errorAlert">{{$message}}</p>
                    @enderror

                    <div class="text-box">
                        <label class="text-label" for="">{{__('Gender')}}</label>
                        @foreach ($genders as $gender)
                            <input class="radio-input" type="radio" name="{{__('Gender_')}}" id="{{ $gender->gender_desc }}" value="{{ $gender->id }}"
                                @error(__('Gender_')) is-invalid @enderror>
                                @if ($gender->gender_desc == "Male")
                                <label for="{{ $gender->gender_desc }}">{{__('Male')}}</label>
                            @elseif($gender->gender_desc == "Female")
                                <label for="{{ $gender->gender_desc }}">{{__('Female')}}</label>
                            @endif
                        @endforeach
                    </div>

                    @error(__('Gender_'))
                        <p class="errorAlert">{{$message}}</p>
                    @enderror

                    <div class="text-box">
                        <label class="text-label" for="{{__('Password_')}}">{{__('Password')}}</label>
                        <input class="text-input" type="password" name="{{__('Password_')}}" id="{{__('Password_')}}"
                            @error(__('Password_')) is-invalid @enderror>
                    </div>

                    @error(__('Password_'))
                        <p class="errorAlert">{{$message}}</p>
                    @enderror
                </div>

                <div class="right-signup-content">
                    <div class="text-box">
                        <label class="text-label" for="{{__('Middle_Name')}}">{{__('Middle Name')}}</label>
                        <input class="text-input" type="text" name="{{__('Middle_Name')}}" id="{{__('Middle_Name')}}"
                            @error(__('Middle_Name')) is-invalid @enderror>
                    </div>

                    @error(__('Middle_Name'))
                        <p class="errorAlert">{{$message}}</p>
                    @enderror

                    <div class="text-box">
                        <label class="text-label" for="{{__('Email_Address')}}">{{__('Email Address')}}</label>
                        <input class="text-input" type="email" name="{{__('Email_Address')}}" id="{{__('Email_Address')}}"
                            @error(__('Email_Address')) is-invalid @enderror>
                    </div>

                    @error(__('Email_Address'))
                        <p class="errorAlert">{{$message}}</p>
                    @enderror

                    <div class="text-box">
                        <label class="text-label" for="{{__('Role_')}}">{{__('Role')}}</label>
                        <select  class="text-input" name="{{__('Role_')}}" id="{{__('Role_')}}"
                            @error(__('Role_')) is-invalid @enderror>
                            @foreach ($roles as $role)
                            <option value="{{ $role->id }}">{{ $role->role_desc }}</option>
                            @endforeach
                        </select>
                    </div>

                    @error(__('Role_'))
                        <p class="errorAlert">{{$message}}</p>
                    @enderror

                    <div class="text-box">
                        <label class="text-label" for="{{__('Display_Picture')}}">{{__('Display Picture')}}</label>
                        <input type="file" name="{{__('Display_Picture')}}" id="{{__('Display_Picture')}}"
                            @error(__('Display_Picture')) is-invalid @enderror>
                    </div>

                    @error(__('Display_Picture'))
                        <p class="errorAlert">{{$message}}</p>
                    @enderror
                </div>
            </div>

            <input class="submit-btn" type="submit" value="{{__('Sign Up')}}">
        </form>
    </div>
@endsection
